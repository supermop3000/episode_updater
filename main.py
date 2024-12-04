# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from shotgun_api3 import Shotgun
import os
import re

def connect_to_shotgrid():
    # Example usage
    SERVER_PATH = MW_PYTHON_SHOTGRID_SERVER
    SCRIPT_NAME = MW_PYTHON_SHOTGRID_NAME
    SCRIPT_KEY = MW_PYTHON_SHOTGRID_KEY

    sg = Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)

    return sg

def get_project_shots(sg, project_id):
    # Find the project with the given name
    project = sg.find_one("Project", [['id', 'is', project_id]], ["id", "name"])

    project_shots = sg.find(
        "Shot",
        [['project', 'is', project]],
        ["id", "code", "project.Project.name", "project.Project.id",
         "sg_sequence.Sequence.sg_episode",
         "sg_sequence.Sequence.sg_episode.CustomEntity01.sg_status_list",
         "sg_sequence.Sequence.episode"]
    )

    return project_shots

def update_episode_data(sg, project_id):
    old_episode_dict = {}
    new_episode_dict = {}

    episode_status_update_only = []
    episode_created = []
    sequence_updated = []

    # GET SET OF UNIQUE OLD EPISODES
    old_episodes = sg.find("CustomEntity01", [['project.Project.id', 'is', project_id]], ["id", "code", "sg_status_list"])
    for old_episode in old_episodes:
        code = old_episode['code']
        old_episode_dict[code] = {'old_episode_id': old_episode['id'], 'sg_status_list': old_episode['sg_status_list']}

    # GET SET OF UNIQUE NEW EPISODES
    new_episodes = sg.find("Episode", [['project.Project.id', 'is', project_id]],
                           ["id", "code", "sg_status_list"])
    for new_episode in new_episodes:
        code = new_episode['code']
        new_episode_dict[code] = {'id': new_episode['id'], 'sg_status_list': new_episode['sg_status_list']}

    # GO THROUGH AND EITHER UPDATE NEW EPISODE STATUSES TO MATCH OLD. AND IF NEW EPISODE DOESN'T EXIST THEN CREATE IT.
    for old_epi in old_episode_dict:
        if old_epi in new_episode_dict:
            print("EPISODE - " + old_epi + " ALREADY EXISTS JUST UPDATE STATUS")
            new_episode_id = new_episode_dict[old_epi].get('id')
            new_status = old_episode_dict[old_epi].get('sg_status_list')
            sg.update("Episode", new_episode_id, {"sg_status_list": new_status})
            episode_status_update_only.append(old_epi)

        else:
            new_status = old_episode_dict[old_epi].get('sg_status_list')
            print("EPISODE - " + str(old_epi) + " NEEDS TO BE CREATED IN NEW EPISODE ENTITY")
            # Define the episode data
            episode_data = {
                "code": old_epi,  # The episode code or name
                "project": {"type": "Project", "id": project_id},  # The project ID to which the episode belongs
                "sg_status_list": new_status,  # The initial status of the episode
                "description": "episode created by episode backfill operation"
            }

            episode_created.append(old_epi)
            # Create a new episode
            sg.create("Episode", episode_data)

    new_episodes = sg.find("Episode", [['project.Project.id', 'is', project_id]],
                           ["id", "code", "sg_status_list"])

    sequences = sg.find("Sequence", [['project.Project.id', 'is', project_id], ['sg_episode', 'is_not', None]],
                           ["id", "code", "sg_status_list", "sg_episode", "episode"])

    count = 1
    seq_count = len(sequences)
    for seq in sequences:
        if seq['sg_episode'] is not None:
            old_seq_epi = seq['sg_episode']['name']

        if seq['sg_episode'] is not None:
            if seq["episode"] is None:
                seq_id = seq['id']

                episode_data = sg.find_one("Episode", [['project.Project.id', 'is', project_id], ['code', 'is', old_seq_epi]],
                        ["id", "code", "sg_status_list", "sg_episode", "episode"])

                sequence_updated.append(old_seq_epi)
                sg.update("Sequence", seq_id, {"episode": episode_data})

                print("Sequence " + str(count) + " of " + str(seq_count) + " sequences UPDATED")

            else:
                print("Sequence " + str(count) + " of " + str(seq_count) + " sequences SKIPPED")

            count += 1

    sequence_updated = sorted(set(sequence_updated))
    episode_created = sorted(set(episode_created))
    episode_status_update_only = sorted(set(episode_status_update_only))

    # print("***********************************************************")
    print("EPISODES CREATED")
    print(episode_created)
    print("EPISODES UPDATED")
    print(episode_status_update_only)
    print("SEQUENCES LINKED")
    print(sequence_updated)
    # print("***********************************************************")

    shots_that_need_updates = []
    shots_ids_that_need_updates = []
    episodes_to_create = []

    project_shots = get_project_shots(sg, project_id)

    for shot in project_shots:

        old_episode = shot['sg_sequence.Sequence.sg_episode']
        if old_episode is not None:
            old_episode_name = shot['sg_sequence.Sequence.sg_episode']['name']
            old_episode_status = shot['sg_sequence.Sequence.sg_episode.CustomEntity01.sg_status_list']
        new_episode = shot['sg_sequence.Sequence.episode']
        shot_code = shot['code']
        shot_id = shot['id']

        if new_episode is None:
            if old_episode is not None:
                print("OLD EPISODE DATA EXISTS NEED TO COPY TO NEW EPISODE DATA")
                print("OLD EPISODE NAME")
                print(old_episode_name)
                print(old_episode_status)

                if old_episode_name not in episodes_to_create:
                    episodes_to_create.append(old_episode_name)

                shots_that_need_updates.append(shot_code)
                shots_ids_that_need_updates.append(shot_id)

    print("SHOTS THAT NEED UPDATES")
    print(shots_that_need_updates)
    print("EPISODES THAT NEED CREATION OR LINKING")
    print(episodes_to_create)
    # print("__________________________________")

# Function to batch project IDs
def batch_project_ids(projects, batch_size):
    project_ids = [project['id'] for project in projects]

    for i in range(0, len(project_ids), batch_size):
        yield project_ids[i:i + batch_size]

def batch_project_names(projects, batch_size):
    project_names = [project['name'] for project in projects]

    for y in range(0, len(project_names), batch_size):
        yield project_names[y:y + batch_size]

def main():
    # Connect to Shotgrid
    sg = connect_to_shotgrid()

    # Go through each project
    # Get a set of old episode names
    #   - Using this set compare it to the new episode names. Create new episodes for any that don't already exist (pass episode status)
    #   - For any episodes that do exist then update their status to match
    # Find all shots within the project that are missing new episode info
    # Go through each shot and link the sequence to the new episode matching the old episode

    # NOTES
    # - This will only update the episode value for shots that already had episode information stored in the old episode entity
    # - This will only update the episode value for shots that already were linked to a sequence
    # - Get list of shots with no sequence value and no episode value
    # - Get list of shots with sequence value and no old episode value (I imagine this is none)
    # - Get list of shots with no sequence value and an old episode value (I imagine this is none)

    # all_projects = sg.find("Project",
    #                     [],
    #                     ["id",
    #                      "code",
    #                      "name",
    #                      "sg_status_list"
    #                      ])

    # print(all_projects)
    # print(len(all_projects))


    path = '/mnt/nas1/JOBS/COY/205/breakout/COY_205_553_0040_EL01_V001/COY_205_553_0040_EL01_V001.[01041-01245].exr'
    # path = '/mnt/nas1/JOBS/COY/205/breakout/COY_205_553_0040_EL01_V001/COY_205_553_0040_EL01_V001.mov'

    directory, filename = os.path.split(path)
    filename_no_ext, ext = os.path.splitext(filename)
    filename_no_frames = re.sub(r'\[\d+-\d+\]', '', filename_no_ext)

    # Extract frame range using regex
    match = re.search(r'\[(\d+)-(\d+)\]', filename_no_ext)
    if match:
        first_frame = int(match.group(1))
        last_frame = int(match.group(2))
    else:
        first_frame = last_frame = None

    if ext == '.mov':
        # Build output structure
        out_clip = {
            'path': os.path.normpath(directory),
            'type': ext,
            'first_frame': first_frame,
            'last_frame': last_frame,
            'path_to_frames': os.path.normpath(path),
        }

    else:
        frame_range_format = f"{'#' * (len(str(first_frame)) + 1)}"

        # Build output structure
        out_clip = {
            'path': os.path.normpath(directory),
            'type': ext,
            'first_frame': first_frame,
            'last_frame': last_frame,
            'path_to_frames': os.path.normpath(
                os.path.join(directory, f"{filename_no_frames}{frame_range_format}{ext}")),
        }

    print(directory)
    print(filename)
    print(filename_no_ext)
    # print(frame_range_format)
    print(out_clip)





    # all_projects = sg.find(
    #     "Note",
    #     [['sg_status_list', 'is', "cmpt"]],
    #     ["id", "code", "project.Project.name", "created_by.HumanUser.login", "updated_by.HumanUser.login"]
    # )
    #
    # print(len(all_projects))

    # login_values = [note['created_by.HumanUser.login'] for note in all_projects]
    # updated_values = [note['updated_by.HumanUser.login'] for note in all_projects]
    #
    # # Print the list of login values
    # print(login_values)
    # print(updated_values)

    # Using the function to divide project IDs into batches of 20
    # project_id_batches = list(batch_project_ids(all_projects, 100))
    # project_name_batches = list(batch_project_names(all_projects, 100))

    # Printing the batches
    # for i, batch in enumerate(project_id_batches):
    #     print(f"Batch {i + 1}: {batch}")
    #
    # for y, name_batch in enumerate(project_name_batches):
    #     print(f"Batch {y + 1}: {name_batch}")
    #
    # print("TEST")
    # print(project_id_batches[0])

    # project_id = 8085

    # Batch1 = [63, 65, 66, 67, 68, 69, 70, 71, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 93, 94, 95, 96,
    #  97, 100, 101, 102, 103, 104, 105, 106, 107, 111, 112, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
    #  126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 141, 142, 143, 144, 145, 147, 148, 149, 150,
    #  151, 152, 153, 154, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 200, 201, 202, 203, 204, 205, 206,
    #  207, 208]

    # Batch2 = [209, 210, 211, 212, 213, 214, 215, 217, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233,
    #     234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 259, 260,
    #     261, 262, 263, 264, 265, 266, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283,
    #     284, 286, 287, 288, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307,
    #     308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319]

    # Batch3 = [320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341,
    #     342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363,
    #     365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387,
    #     388, 421, 422, 424, 425, 426, 427, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444,
    #     445, 447, 448, 449, 450, 451, 452, 453, 454, 487, 488, 489]

    # Batch4 = [490, 491, 492, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512,
    #     513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 533, 534, 535,
    #     536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557,
    #     558, 559, 593, 594, 595, 596, 598, 599, 600, 601, 602, 603, 607, 608, 609, 610, 611, 613, 614, 615, 616, 617,
    #     618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629]

    # Batch5 = [630, 631, 632, 633, 634, 635, 636, 637, 638, 640, 641, 642, 643, 644, 645, 646, 647, 649, 650, 651, 652, 655,
    #     656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 675, 676, 677,
    #     678, 679, 680, 681, 682, 683, 684, 717, 718, 719, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 744,
    #     745, 746, 747, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 797, 798,
    #     799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809, 810]

    # Batch6 = [811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 854, 855, 856, 889, 890, 922, 955, 988, 1087, 1120, 1153,
    #     1186, 1219, 1252, 1253, 1285, 1286, 1318, 1351, 1384, 1385, 1386, 1387, 1417, 1450, 1516, 1549, 1582, 1615,
    #     1648, 1681, 1714, 1747, 1780, 1781, 1813, 1846, 1879, 1912, 1945, 1978, 2011, 2012, 2044, 2077, 2110, 2143,
    #     2176, 2209, 2242, 2275, 2308, 2309, 2341, 2374, 2407, 2440, 2441, 2442, 2473, 2474, 2506, 2507, 2508, 2510,
    #     2539, 2573, 2605, 2638, 2671, 2704, 2737, 2770, 2803, 2804, 2836, 2869, 2870, 2871, 2902, 2968, 2969, 3001,
    #     3034, 3067, 3100, 3133, 3134, 3166]

    # Batch7 = [3199, 3232, 3265, 3266, 3298, 3331, 3332, 3364, 3397, 3430, 3496, 3529, 3562, 3595, 3596, 3628, 3661, 3694,
    #     3727, 3760, 3793, 3794, 3795, 3826, 3859, 3860, 3892, 3893, 3894, 3925, 3958, 3991, 4024, 4057, 4090, 4123,
    #     4156, 4189, 4190, 4191, 4222, 4255, 4288, 4321, 4322, 4354, 4387, 4420, 4453, 4486, 4519, 4552, 4585, 4618,
    #     4651, 4684, 4717, 4750, 4783, 4816, 4882, 4883, 4915, 4916, 4948, 4981, 4982, 5014, 5047, 5048, 5080, 5113,
    #     5146, 5179, 5213, 5245, 5278, 5311, 5344, 5377, 5378, 5410, 5443, 5476, 5509, 5542, 5575, 5576, 5608, 5641,
    #     5642, 5674, 5707, 5708, 5709, 5740, 5741, 5742, 5773, 5806, 5839, 5872, 5905, 5938, 5971, 5974, 5975, 6004, 6037, 6070, 6103, 6104, 6105, 6136, 6137, 6169, 6202, 6203,
    #     6235, 6268, 6301, 6334, 6367, 6368, 6400, 6466, 6499, 6500, 6533, 6565, 6598, 6631, 6664, 6665, 6697, 6730,
    #     6763, 6796, 6829, 6862, 6864, 6865, 6895, 6896, 6898, 6928, 6961, 6994, 7027, 7060, 7093, 7126, 7159, 7192,
    #     7193, 7225, 7258, 7291, 7292, 7325, 7357, 7390, 7423, 7424, 7456, 7489, 7522, 7523, 7555, 7588, 7589, 7621,
    #     7654, 7687, 7720, 7753, 7786, 7819, 7852, 7918, 7919, 7951, 7952, 7984, 8017, 8050, 8083, 8084, 8085, 8116,
    #     8149, 8150, 8182, 8215, 8216, 8217, 8248, 8249, 8281, 8282, 8314, 8347, 8348, 8349, 8350, 8380, 8413, 8414, 8479, 8512, 8545, 8578, 8579, 8611, 8644, 8677, 8710, 8743,
    #     8776, 8809, 8811, 8842, 8875, 8876, 8877, 8908, 8941, 8942, 8974, 8975, 8976, 9007, 9040, 9041, 9073, 9074,
    #     9106, 9139, 9140, 9141, 9142, 9172, 9205, 9238, 9271, 9272, 9273, 9304, 9337, 9339, 9370, 9403, 9436, 9469,
    #     9502, 9568, 9601, 9634, 9635]
    #
    # for project_id in Batch7:
    #     print("**********************************************************UPDATING PROJECT ID: " + str(project_id) + " ***********************************************************************************")
    #     update_episode_data(sg, project_id)
    #     print("**********************************************************UPDATE COMPLETE FOR PROJECT ID: " + str(
    #         project_id) + " ***********************************************************************************")

    # update_episode_data(sg, project_id)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
