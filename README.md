<div align="center">

# PRNU Camera Fingerprint Analysis

### Camera source identification using PRNU, PCE and EXIF metadata

A Python desktop application for experimentally analyzing whether a questioned photograph may originate from a specific camera or smartphone.

<br>

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Image%20Processing-green?logo=opencv)](https://opencv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Experimental-orange)](#forensic-use-disclaimer)

[English](README.md) · [Türkçe](README_TR.md)

</div>

---

## Overview

**PRNU Camera Fingerprint Analysis** is an experimental digital image forensics application developed to investigate the following question:

> Was this photograph captured by the claimed camera or smartphone?

The application creates a reference sensor fingerprint from a collection of photographs and compares it with the noise residual extracted from a questioned image.

It combines two analysis layers:

* **Optical analysis:** PRNU fingerprint comparison using PCE
* **Metadata analysis:** EXIF make, model, software and image information comparison

> [!WARNING]
> This project is intended for education, research and experimental analysis. Its results must not be treated as standalone forensic evidence or a legal conclusion.

## Main Features

* PRNU-based camera sensor fingerprint extraction
* RGB multi-channel noise processing
* Daubechies db8 wavelet denoising
* Fourier-based artifact reduction
* Peak-to-Correlation Energy calculation
* Pearson correlation calculation
* EXIF metadata comparison
* JPEG compression warnings
* HEIC image support
* Adaptive analysis threshold for Apple devices
* Saved fingerprint management
* TXT analysis report generation
* Tkinter graphical user interface

## Application Workflow

```text
Reference photographs
        │
        ▼
Noise residual extraction
        │
        ▼
Reference PRNU fingerprint
        │
        ├───────────────┐
        ▼               ▼
Questioned image     EXIF metadata
        │               │
        ▼               ▼
 PCE comparison    Model comparison
        │               │
        └───────┬───────┘
                ▼
         Experimental result
```

## Installation

```bash
git clone https://github.com/erenkocak1/prnu-camera-fingerprint-analysis.git
cd prnu-camera-fingerprint-analysis
pip install -r requirements.txt
python prnu_v4.py
```

## Basic Usage

1. Collect approximately **25–50 original photographs** from the reference device.
2. Click **Referans Klasörü Seç & İşle** to generate the fingerprint.
3. Select or load the saved reference fingerprint.
4. Click **Şüpheli Fotoğrafı Seç ve Analiz Et**.
5. Review the PCE, Pearson, EXIF and image-quality results.
6. Generate a TXT analysis report when required.

> [!IMPORTANT]
> Images transferred through WhatsApp, Instagram or similar services may be resized, recompressed or stripped of EXIF data. Original files should be used whenever possible.

## Decision Thresholds

|    PCE value | Experimental interpretation |
| -----------: | --------------------------- |
|     Below 20 | Negative                    |
|        20–59 | Inconclusive or weak        |
| 60 and above | Strong correlation          |

For reference devices detected as Apple products, the program currently applies an experimental adaptive threshold of `30`.

These values are implementation choices and have not been validated as universal forensic thresholds.

<details>
<summary><strong>Technical analysis details</strong></summary>

### RGB Multi-Channel Processing

The red, green and blue channels are processed independently. The green channel receives additional weight based on the Bayer sensor layout.

### Wavelet Denoising

Daubechies db8 wavelet decomposition is used to estimate the image content. The denoised image is subtracted from the original image to obtain a noise residual.

### Artifact Reduction

Row and column means, JPEG block-related patterns and selected periodic frequency components are reduced before correlation.

### PCE Comparison

Peak-to-Correlation Energy is calculated from the cross-correlation surface between the stored reference fingerprint and the questioned image noise residual.

### EXIF Comparison

Available fields such as camera make, model, software, resolution and capture information are compared with the reference metadata.

</details>

<details>
<summary><strong>Supported formats and generated files</strong></summary>

### Supported Formats

* JPEG
* PNG
* HEIC
* WEBP

### Generated Files

```text
parmak_izleri/
├── fp_DEVICE_MODEL.npy
└── meta_DEVICE_MODEL.json
```

The `.npy` file stores the generated fingerprint. The `.json` file may contain device metadata and should not be committed to a public repository.

</details>

## Known Limitations

* EXIF metadata may be removed, modified or forged.
* Different devices using similar processing pipelines may share non-unique artifacts.
* Images that have been cropped, resized or recompressed may produce unreliable scores.
* Screenshots are unsuitable for camera sensor fingerprint comparison.
* Computational photography may suppress or alter PRNU signals.
* False-positive and false-negative results may occur.
* The application has not been validated on a large controlled forensic dataset.
* It is not a certified forensic examination product.

## Privacy

Do not upload the following items to the public repository:

```text
Private reference photographs
Questioned photographs
Generated .npy fingerprints
Generated metadata JSON files
Analysis reports containing personal information
```

Recommended `.gitignore` entries:

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/

parmak_izleri/
*.npy

*.log
.DS_Store
Thumbs.db
```

I would **not** ignore every `*.json` file globally, because JSON configuration files may be added to the project later. Ignoring `parmak_izleri/` is sufficient for the metadata currently generated there.

## Roadmap

* Modular project structure
* Progress indicator and cancellation support
* Batch questioned-image analysis
* CSV and PDF report export
* PCE distribution visualization
* Automated testing
* Device-specific threshold calibration
* Controlled benchmark dataset
* ROC, false-positive and false-negative evaluation

## Forensic Use Disclaimer

This software is provided for educational, research and experimental purposes.

Its results must not be used alone as definitive forensic evidence, expert testimony or a legal conclusion. A proper forensic examination should additionally address file integrity, cryptographic hashes, chain of custody, acquisition methods, controlled validation, error rates and independent expert review.

## Author

**Yusuf Eren Koçak**

[GitHub Profile](https://github.com/erenkocak1)

## License

This project is licensed under the [MIT License](LICENSE).
