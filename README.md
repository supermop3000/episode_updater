# ShotGrid Episode Sync Utility

This Python script provides a utility for synchronizing episode data between legacy and current ShotGrid entities. It ensures episode statuses, sequences, and shots are properly updated and linked, reducing manual data entry and potential errors.

---

## Features

- **Connect to ShotGrid**: Uses the ShotGrid API to interact with project, episode, sequence, and shot entities.
- **Episode Syncing**:
  - Updates new episodes with statuses from legacy episodes.
  - Creates missing episodes in the new episode entity.
- **Sequence Linking**:
  - Ensures sequences are linked to their corresponding episodes.
- **Shot Validation**:
  - Identifies shots requiring updates to their episode data.
- **Batch Processing**:
  - Handles large numbers of projects efficiently by processing them in batches.

---

## Requirements

- Python 3.6+
- ShotGrid API (`shotgun_api3`)
- Standard Python libraries: `os`, `re`, `datetime`

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd shotgrid-episode-sync
   ```

2. **Install Dependencies**:
   ```bash
   pip install shotgun-api3
   ```

3. **Set Environment Variables**:
   Configure the following environment variables for ShotGrid API access:
   - `MW_PYTHON_SHOTGRID_SERVER`
   - `MW_PYTHON_SHOTGRID_NAME`
   - `MW_PYTHON_SHOTGRID_KEY`

---

## How to Use

### 1. Connect to ShotGrid
The script connects to ShotGrid using the `connect_to_shotgrid()` function. Ensure the environment variables are set correctly for authentication.

### 2. Update Episode Data
Run the `update_episode_data(sg, project_id)` function to:
- Synchronize episode statuses.
- Create new episodes if they don't exist in the current entity.
- Update sequences to link them with the correct episodes.

### 3. Validate Shots
The script identifies shots that:
- Have missing sequence or episode data.
- Need their sequence linked to the appropriate episode.

### 4. Process Multiple Projects
Use the `batch_project_ids` or `batch_project_names` functions to divide projects into manageable batches for processing.

### 5. Run the Script
To execute the script:
```bash
python script_name.py
```
Replace `script_name.py` with the filename.

---

## Example Output

The script provides detailed logs, such as:
- Episodes created:
  ```
  EPISODES CREATED
  ['EP001', 'EP002']
  ```
- Episodes updated:
  ```
  EPISODES UPDATED
  ['EP003']
  ```
- Sequences linked:
  ```
  SEQUENCES LINKED
  ['SEQ001', 'SEQ002']
  ```
- Shots requiring updates:
  ```
  SHOTS THAT NEED UPDATES
  ['SHOT001', 'SHOT002']
  ```

---

## Configuration

### ShotGrid Entities
- **Legacy Episodes**: `CustomEntity01`
- **Current Episodes**: `Episode`
- **Sequences**: `Sequence`
- **Shots**: `Shot`

### Environment Variables
Set the following variables:
- `MW_PYTHON_SHOTGRID_SERVER`: The ShotGrid server URL.
- `MW_PYTHON_SHOTGRID_NAME`: The script's name.
- `MW_PYTHON_SHOTGRID_KEY`: The script's API key.

---

## Future Enhancements

- Add logging for better tracking and debugging.
- Enhance batch processing with multi-threading.
- Extend support to additional ShotGrid entities.
- Add a command-line interface for easier configuration.

---

## License
This project is open-source and available under the [MIT License](LICENSE).

---

