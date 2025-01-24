from shotgun_api3 import Shotgun
import os
import re

# Environment variables for ShotGrid connection
SERVER_PATH = os.getenv("MW_PYTHON_SHOTGRID_SERVER")
SCRIPT_NAME = os.getenv("MW_PYTHON_SHOTGRID_NAME")
SCRIPT_KEY = os.getenv("MW_PYTHON_SHOTGRID_KEY")

def connect_to_shotgrid():
    """Establish a connection to ShotGrid."""
    return Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)

def get_project_shots(sg, project_id):
    """Retrieve all shots for a given project."""
    project = sg.find_one("Project", [['id', 'is', project_id]], ["id", "name"])
    return sg.find(
        "Shot",
        [['project', 'is', project]],
        ["id", "code", "project.Project.name", "project.Project.id",
         "sg_sequence.Sequence.sg_episode",
         "sg_sequence.Sequence.sg_episode.CustomEntity01.sg_status_list",
         "sg_sequence.Sequence.episode"]
    )

def batch_list(items, batch_size):
    """Yield successive batches from a list."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def update_episode_data(sg, project_id):
    """Update episodes and link sequences in ShotGrid for the given project."""
    old_episode_dict = {}
    new_episode_dict = {}

    episode_status_update_only = []
    episode_created = []
    sequence_updated = []

    # Retrieve old episodes
    old_episodes = sg.find("CustomEntity01", [['project.Project.id', 'is', project_id]], ["id", "code", "sg_status_list"])
    for old_episode in old_episodes:
        old_episode_dict[old_episode['code']] = {
            'old_episode_id': old_episode['id'],
            'sg_status_list': old_episode['sg_status_list']
        }

    # Retrieve new episodes
    new_episodes = sg.find("Episode", [['project.Project.id', 'is', project_id]], ["id", "code", "sg_status_list"])
    for new_episode in new_episodes:
        new_episode_dict[new_episode['code']] = {
            'id': new_episode['id'],
            'sg_status_list': new_episode['sg_status_list']
        }

    # Update or create episodes
    for old_epi, old_data in old_episode_dict.items():
        if old_epi in new_episode_dict:
            new_episode_id = new_episode_dict[old_epi]['id']
            sg.update("Episode", new_episode_id, {"sg_status_list": old_data['sg_status_list']})
            episode_status_update_only.append(old_epi)
        else:
            sg.create("Episode", {
                "code": old_epi,
                "project": {"type": "Project", "id": project_id},
                "sg_status_list": old_data['sg_status_list'],
                "description": "Episode created by backfill operation"
            })
            episode_created.append(old_epi)

    # Update sequences with episodes
    sequences = sg.find("Sequence", [
        ['project.Project.id', 'is', project_id],
        ['sg_episode', 'is_not', None]
    ], ["id", "code", "sg_status_list", "sg_episode", "episode"])

    for idx, seq in enumerate(sequences, start=1):
        if seq['sg_episode'] and not seq['episode']:
            old_seq_epi = seq['sg_episode']['name']
            episode_data = sg.find_one("Episode", [
                ['project.Project.id', 'is', project_id],
                ['code', 'is', old_seq_epi]
            ], ["id"])
            if episode_data:
                sg.update("Sequence", seq['id'], {"episode": episode_data})
                sequence_updated.append(old_seq_epi)

    # Remove duplicates and sort
    episode_status_update_only = sorted(set(episode_status_update_only))
    episode_created = sorted(set(episode_created))
    sequence_updated = sorted(set(sequence_updated))

    # Print results
    print("EPISODES CREATED:", episode_created)
    print("EPISODES UPDATED:", episode_status_update_only)
    print("SEQUENCES LINKED:", sequence_updated)

def main():
    sg = connect_to_shotgrid()

    # Example: Retrieve all projects (modify filters as needed)
    all_projects = sg.find("Project", [], ["id", "name"])
    batch_size = 100

    # Batch process projects
    for project_batch in batch_list(all_projects, batch_size):
        for project in project_batch:
            print(f"Processing project: {project['name']} (ID: {project['id']})")
            update_episode_data(sg, project['id'])
            print(f"Completed updates for project: {project['name']} (ID: {project['id']})")

if __name__ == '__main__':
    main()
