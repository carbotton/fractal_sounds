## [1.4.2] - 2024-04-23
### Added
  - README file now has all the steps for replicate the proyect
  
  - Removed comments
  
  - Updated_reaper_project
### Fixed
- **To Player**:
  - Fixed minor bugs

## [1.4.2] - 2024-03-25
### Added
- **Fractal /Interpreter**:
  - Fixed double zoom concurrency problem
- **Player**:
  - Fixed concurrency problem when a new gesture is detected

## [1.4.1] - 2024-03-10
### Added
- **To Player**:
  - Fixed indexing to maintain the same index for each part of the song.
  - Implemented functionality to move used parts to a different folder for better management.

- **To Generator and Player**:
  - Enhanced gradient image generation code for visual effects.
  - Introduced shared memory usage across components, moving away from dto for inter-component communication.

- **To Documentation**:
  - Added .gitignore file to exclude `__pycache__` and `.pyc` files.
  - Created comprehensive README and CHANGELOG documents.

### Changed
- **To Player**:
  - Updated PID control within the player for precise audio control.
  - Unified zoom click and hand approaching behaviors for consistent user interaction.

- **To Interpreter and Other Components**:
  - Removed comments for cleaner code and improved readability in Fractal, Interpreter, Player, and GestureDetector.

### Fixed
- **To Player**:
  - Corrected `self.dto['cursor_position'][0]` to fix cursor tracking issues.

- **To GestureTrainer and Scene Command**:
  - Fixed issues in `GestureTrainer` and optimized scene commands by grouping functions and removing unnecessary comments.

### Merges
- Merged various feature branches to integrate new functionalities and fixes into main project streams (`feature/beta_0`, `beta/version_final`).

### Cleanup
- Removed unnecessary comments across multiple components for clarity and maintenance (Fractal, Interpreter, Player, GestureDetector, Generator, shared_memory)

### Version Control Management
- Updated `.gitignore` for new MIDI files and streamlined project directory management.

### Documentation
- Updated main script for executing the program and creating songs, simplifying user interactions.
## [1.4.0] - 2024-02-10
### Added
- **To Player**:
  - Implemented functionality to restart the song automatically upon completion.

- **To Generator**:
  - Added `delete_folders` and `generate_chords_and_melody` functions to enhance music generation capabilities.

### Changed
- **To Generator**:
  - Made adjustments for channel configurations, concatenation, and appending processes to streamline audio file handling.

### Documentation
- **To Documentation**:
  - Added new architectural diagrams to aid in understanding the project structure.

### Merges
- Merged updates from main branch, including solutions for channel issues, to maintain consistency across branches.



## [1.2.1] - 2024-01-31
### Added
  - Branch with fractal logic with cuda merged to main

## [1.2.0] - 2024-01-30
### Added
- **To Generator.py**:
  - Added melody to the list of folder paths for project organization.
  - Added functionality to append MIDIs for each structure's letter and save them to disk.
  - Path logic to handle MIDI structures and create folders according to structure parts.

- **To Reaper Project**:
  - Configured OSC and Python for dynamic interaction.
  - Added OSC address examples for better integration.
  - Implemented OSC communication to change track volume dynamically.
  - Developed solo track functionality via OSC commands (`def solo_track()`).

- **To Player Main**:
  - Introduced loop tracks when user does not change movement, enhancing interactive performance.
  - Added logging level adjustments and functions to check for movement changes.
  - Integrated loop track testing and validation functionalities.

### Changed
- **To Generator.py**:
  - Updated `requirements.txt` for new dependencies.
  - Refined folder logic for improved file management and structure handling.

- **General Configuration**:
  - Updated `.gitignore`, streamlined clean-up processes.

### Fixed
- **To Player Main**:
  - Corrected player's change detection mechanism.

### Testing
- **General Testing**:
  - Conducted tests on sliders without implementation to assess non-functional aspects.
  - Performed comprehensive tests in notebook with OSC Reaper integrations.

### Cleanup
- **To Generator.py**:
  - Executed multiple cycles of MIDI deletion for structure optimization.
  - General clean-up to streamline operations and folder logic changes.

### Merges
- Merged various branches to consolidate features and fixes related to Reaper interactions and main project enhancements

## [1.1.1] - 2024-01-29
### Added
- **To Generator.py**:
  - Added melody to the list of folder paths.

### Changed
- **To Generator.py**:
  - Updated `requirements.txt` for new dependencies.

- **To Reaper Project**:
  - Configured OSC and Python for communication.
  - Implemented OSC communication to change track volume.
  - Added OSC address examples.
  - Defined `solo_track()` for OSC solo track functionality.

### Tests
- **To Player Main**:
  - Conducted tests for detecting movement speed.
  - Tested idea of taking loop sections in PLAYER MAIN.
  - Conducted general testing and prepared for PR review.

### Configuration and Integration
- **To OSC Configuration**:
  - Tested slider functionality without implementation.


## [1.1.0] - 2023-10-19
### Added
- To config.py:
  - Emotion added
- Added gesture detector class
- Interpreter now works with gesture detector as parameter
- To generator:
    * added groove vae
    * added concatenate foos
    * added drum temperature
    * generate_chords_and_melody
- To player:
  * modify pitch
  * modify emotion
- To parameters dto:
  * added emotion

## [1.0.3] -   2023-09-13
### Added
- **To Generator.py**:
  - Added `generate_bass()` function.
  - Integrated new pretrained models.
  - Implemented `generate_melody` and `generate_drums` functions.
  - Initial tests for `generate_structure`.
  - Docstrings for all methods in `Generator.py`.
  - Completed full debug and testing of `Generator` in `main.ipynb`.
  - Utilized `melody_rnn_generate` with `config=basic_rnn` for backing up `generate_melody`.
  - Employed `piano_roll` for primer melody and pitches in `generate_melody`.
  - Developed new functions for concatenating MIDIs using the `MidiFile` class.
  - Configured list of instruments as a parameter.
  - Integrated `improv_rnn_generate` with all configuration options in `magenta_commands`.

### Changed
- **To Generator.py**:
  - Extensive refactoring and addition of new classes.
  - Tested and modified `concat_midi`; changes in `generate_structure` to new approach.
  - Integrated instrument channel changes in `Generator` and updated `test_notebook`.

### Fixed
- **To Generator.py**:
  - Corrections made to methods in the generator.
  - Solved issues with `concatenar`; updated usage of `pretty_midi`.
  - Fixed `extract_single_channel`.

### Configuration and Integration
- **To .gitignore**:
  - Updated `.gitignore` files multiple times to exclude unnecessary files.

### Merges
- Merged `feature/interactive_sliders` and `feature/generate_midi_files` into the main branch, consolidating features and fixes.

## [1.0.2] - 2023-08-10
### Added
2 mayor changes:

  - now the classes interpreter and player can exchange information between them
  - interactive slider (and some foos) now modify the midi msg output

## [1.0.1] - 2023-07-23
### Added
- To config.py:
  - Pretrained model's paths
  - Midi structure
  - Bass primer melody
  - Midi steps number
- New pretrained models to pretrained_models folder + info.md
- generate_bass() for generate_midi_files in Generator.py

## [1.0.0] - 2023-07-21
### Added
- Initial release of the project
- barra de progreso para las flechitas o dibujar la linea de una
- hay un deadlock en las flechas pareceria.
- integrar la deteccion de dedo indice al modulo principal de deteccion
- config los midi channels
- check de la logica de enviar notas
- ver de manipular mejor los colores del fractal
- hacer la generacion de fractal sea una sola vez