# Copilot Instructions

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Context
This is a Django application for analyzing MIT App Inventor (.aia) files to evaluate app usability, with a focus on image and icon quality assessment.

## Key Components
- Django web framework for file upload and analysis interface
- ZIP file extraction for .aia files (which are compressed archives)
- Image processing using Pillow for quality assessment
- Usability evaluation metrics for mobile app interfaces

## Code Style Guidelines
- Follow Django best practices and conventions
- Use class-based views where appropriate
- Implement proper error handling for file uploads
- Include comprehensive documentation for analysis algorithms
- Focus on user-friendly interface design for evaluation workflows

## Special Considerations
- .aia files are ZIP archives containing App Inventor project files
- Images and assets are typically stored in specific subdirectories
- Consider mobile app usability principles in evaluation criteria
- Implement secure file handling for uploads
