# WordPress Media Cleaner 🧹

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)

A powerful tool to clean up WordPress media thumbnails and organize your uploads folder. Automatically identifies and removes duplicate thumbnail images while preserving original uploads.

![App Screenshot](/assets/screenshot.png) <!-- Replace with actual screenshot -->

## Why Use This Tool? 🤔

WordPress generates multiple thumbnail versions for every uploaded image, which can:
- Consume significant storage space
- Slow down backups
- Make manual organization difficult

This script helps you:
✔ Automatically detect and delete thumbnails  
✔ Preserve original uploaded images  
✔ Organize remaining files into clean folders  
✔ Save disk space (often 50-70% reduction)  

## Features ✨

- Intelligent thumbnail detection (supports complex WordPress naming patterns)
- Preview mode to see what will be deleted
- Recursive folder scanning
- Handles multiple image formats (JPG, PNG, WebP, etc.)
- User-friendly GUI with progress logging
- Safe operations (never deletes originals)

## Installation ⚙️

### Prerequisites
- Python 3.8 or higher
- Tkinter (usually included with Python)

### Steps:
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/wordpress-media-cleaner.git
   cd wordpress-media-cleaner