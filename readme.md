# Project Setup

## Prerequisites
- Python 3.11 installed
- [virtualenv](https://pypi.org/project/virtualenv/) (optional but recommended)
- [Streamlit](https://streamlit.io/)

## Setup Instructions

1. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # For macOS/Linux
   venv\Scripts\activate      # For Windows 

2. Install dependencies
    ```bash
    pip install -r requirements.txt


3. Configure Streamlit secrets
- Create a .streamlit folder in the project root.
- Inside it, create a secrets.toml file.
- Paste the environment variables into secrets.toml.


4. Run the application
    ```bash 
    streamlit run app.py

Notes
The secrets.toml file contains environment variables. Please obtain them from the PIC unless this repository is private.

If the repository is private, you may include a toml.example file in the repo for reference.