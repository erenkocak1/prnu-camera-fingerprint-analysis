PRNU Camera Fingerprint Analysis

A desktop application that analyzes whether a photograph was captured by a specific camera or smartphone using PRNU, PCE, and EXIF data.

This project aims to verify image sources by examining the unique noise patterns produced by camera sensors during manufacturing. The system evaluates both the optical sensor fingerprint and the software-based EXIF metadata to provide a more comprehensive analysis result.

Project Purpose

The project mainly aims to answer the following question:

Was this photograph actually captured by the claimed device?

The application creates a sensor fingerprint using reference photographs captured by a suspected device. The noise pattern extracted from a questioned photograph is then compared with this reference fingerprint.

Features
PRNU-based camera sensor fingerprint extraction
RGB multi-channel noise analysis
Daubechies db8 wavelet denoising
Fourier-based periodic artifact removal
PCE calculation
Pearson correlation calculation
EXIF metadata analysis
Reference and questioned image metadata comparison
JPEG compression and quality analysis
HEIC image support
Adaptive PCE threshold for Apple devices
Saving and loading previously generated sensor fingerprints
TXT forensic report generation
Tkinter-based graphical user interface
Technologies
Python
OpenCV
NumPy
PyWavelets
Pillow
Pillow-HEIF
Tkinter
Installation

Clone the repository:

git clone https://github.com/erenkocak1/prnu-camera-fingerprint-analysis.git

Navigate to the project directory:

cd prnu-camera-fingerprint-analysis

Install the required Python packages:

pip install -r requirements.txt

Run the application:

python prnu_v4.py

On some systems, the following command may be required:

python3 prnu_v4.py
Usage
1. Prepare Reference Images

Place approximately 25 to 50 photographs captured by the target device in the same folder.

For more reliable results, the reference images should:

Be copied directly from the original device
Not be transferred through WhatsApp, Instagram, or similar platforms
Preserve their original resolution
Include different scenes and lighting conditions
Avoid completely dark or uniform images
Avoid screenshots or heavily edited images
2. Create a Sensor Fingerprint

After launching the program:

Click Select Reference Folder & Process.
Select the folder containing the reference images.
Wait for the images to be processed.
The generated sensor fingerprint will be saved automatically.

Saved fingerprints are stored in the parmak_izleri directory.

3. Analyze a Questioned Image
Create a new reference fingerprint or load a previously saved fingerprint.
Click Select and Analyze Questioned Image.
Select the photograph to be examined.
Review the PCE, Pearson correlation, EXIF, image quality, and final decision results.
Decision System

Default PCE thresholds in normal mode:

PCE Value	Result
PCE < 20	Negative
20 ≤ PCE < 60	Suspicious / Inconclusive
PCE ≥ 60	Strong match

Apple devices may use a lower adaptive threshold because computational photography and image processing algorithms can suppress the PRNU signal.

Default Apple matching threshold:

PCE ≥ 30

Threshold values can be modified through the application interface.

Analysis Layers
PRNU Analysis

Camera sensors contain microscopic differences in pixel sensitivity that are introduced during manufacturing.

These variations create an invisible noise pattern in photographs. This pattern can be evaluated as the optical fingerprint of the camera sensor.

RGB Multi-Channel Processing

The application processes the red, green, and blue channels separately.

The green channel receives additional weight because Bayer sensor layouts generally contain twice as many green pixels as red or blue pixels.

This approach preserves more sensor information than converting the image directly to grayscale.

Wavelet Denoising

The image is decomposed using the Daubechies db8 wavelet method.

Image content and high-frequency noise components are separated. The denoised image is subtracted from the original image to estimate the sensor noise residual.

Non-Unique Artifact Removal

The extracted residual may contain artifacts that are not unique to a single sensor, including:

JPEG block patterns
Row and column banding
Shared image signal processor artifacts
Lens-related patterns
Periodic processing structures

The application attempts to reduce these common artifacts before comparison.

Fourier Filtering

Periodic sensor lines, lens-related artifacts, and some shared frequency components are detected and filtered in the Fourier frequency domain.

This process aims to reduce false similarities between different devices.

PCE

Peak-to-Correlation Energy measures the similarity between the stored reference fingerprint and the noise pattern extracted from the questioned image.

A higher PCE value generally indicates a stronger correlation.

However, PCE should not be treated as definitive forensic evidence on its own.

Pearson Correlation

Pearson correlation is also calculated as an additional reference value.

It is displayed together with PCE but is not used as the primary decision metric.

EXIF Analysis

The application compares image metadata fields, including:

Make
Model
Software
Image resolution
Capture date
Camera settings
Other available EXIF fields

Combining optical sensor analysis with EXIF metadata provides a broader evaluation than relying on only one method.

Adaptive Apple Mode

Apple devices may apply aggressive computational photography operations such as:

Smart HDR
Deep Fusion
Neural processing
Noise reduction
Multi-frame image fusion

These operations may weaken or suppress the PRNU signal.

When the reference device is identified as an Apple device through EXIF metadata, the application automatically uses a lower PCE matching threshold.

This behavior is experimental and does not guarantee accurate results for every Apple model.

JPEG and Social Media Compression

Platforms such as WhatsApp, Instagram, Facebook, and Telegram may resize or recompress images.

These operations can:

Weaken the PRNU signal
Remove EXIF metadata
Reduce PCE scores
Create false-negative results
Introduce additional compression artifacts

Original image files should be used whenever possible.

Supported File Formats
JPG
JPEG
PNG
HEIC
WEBP

The pillow-heif package is used to open HEIC files.

Generated Files

Sensor fingerprints are stored using the following structure:

parmak_izleri/
├── fp_DEVICE_MODEL.npy
└── meta_DEVICE_MODEL.json

The .npy file contains the generated sensor fingerprint.

The .json file contains the reference image metadata, image count, and additional processing information.

These files may contain device-related or personal metadata and should be reviewed before being uploaded to a public repository.

Project Structure
prnu-camera-fingerprint-analysis/
├── prnu_v4.py
├── requirements.txt
├── README.md
├── README_EN.md
├── .gitignore
└── parmak_izleri/

The parmak_izleri directory may be created automatically when the application is launched.

Forensic Report Generation

After an image is analyzed, the application can generate a TXT report containing:

Analysis date and time
PCE score
Pearson correlation
Threshold values
Number of reference images
JPEG quality estimate
Compression warnings
Reference device model
Questioned image model
Final decision
Detailed EXIF comparison

The generated report is intended for documentation and experimental evaluation purposes.

Known Limitations
Different phones of the same brand and model may contain identical EXIF model information.
Different devices using the same sensor or image-processing pipeline may produce similar artifacts.
Social media compression may significantly damage the PRNU signal.
Screenshots are not suitable for sensor fingerprint analysis.
Edited, resized, filtered, or recompressed images may produce unreliable results.
Apple image-processing systems may significantly suppress the PRNU signal.
The same threshold values may not work equally well for every device.
High PCE values do not automatically prove that two images came from the same physical device.
EXIF metadata can be edited, removed, or forged.
The current implementation has not been validated on a large controlled forensic dataset.
False positives and false negatives may occur.
The application is not a certified commercial forensic examination tool.
Forensic Use Disclaimer

This project was developed for educational, research, and experimental analysis purposes.

The results generated by the application must not be used alone as definitive forensic evidence, expert testimony, or a legal conclusion.

A real forensic examination should additionally consider:

Original file integrity
Cryptographic hash values
Chain of custody
Device acquisition methods
Repeatable testing
Controlled datasets
Known error rates
Validation procedures
Independent expert review
Alternative explanations

The final result should always be evaluated together with other forensic findings.

Privacy

Reference and questioned images may contain personal information, including:

Location data
Device model
Capture date
Camera settings
Software information
Other EXIF metadata

Do not upload private test images, generated sensor fingerprints, or metadata files to a public GitHub repository without reviewing their contents.

Recommended .gitignore Entries

The following files and folders should generally be excluded from Git:

__pycache__/
*.pyc
*.pyo
*.npy
parmak_izleri/
*.json
.env
venv/
.venv/

Be careful when ignoring all .json files if the project later includes legitimate configuration files.

Future Improvements
PDF report generation
Batch analysis of multiple questioned images
CSV export
PCE distribution visualization
Reference dataset quality control
Device-specific threshold calibration
ROC curve calculation
False-positive and false-negative analysis
Automated testing
Command-line interface
Modular project architecture
Logging system
Progress bar for long-running operations
Cancellation support during fingerprint generation
Improved handling of large images
Controlled same-model and different-device experiments
Reproducible benchmark datasets
Contribution

You may fork the repository, make improvements, and submit a pull request.

When reporting an issue, please include:

Operating system
Python version
Image format
Full error message
The action that caused the error
A privacy-safe example scenario, when possible

Do not upload images containing personal or sensitive metadata in public issue reports.

License

No license has currently been assigned to this project.

Until a license is added, permission to use, modify, or redistribute the source code is not explicitly granted.

Developer

Yusuf Eren Koçak

GitHub: erenkocak1

This project was developed for educational and research purposes in the fields of camera sensor fingerprinting, digital image forensics, and source camera identification.
