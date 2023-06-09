# Ellie contour wall research

This subfolder of the StrijpT-Ellie repository contains the experimentation grounds and exploratory code regarding the Contour Wall practical considerations related to its successful implementation, particularly in terms of contour extraction for subsequent image processing. Several methods are being evaluated to determine the optimal technique for this purpose.

## How to run
1. Setup up Python Venv: `python3 -m venv .venv`
2. Activate enviroment: 
   - For Unix: `source .venv/bin/activate`
   - For Windows: `./.venv/Scripts/Activate.ps1`      
3. Install requirements for all research: `python3 -m pip install -r requirements.txt`
4. Run media pipe script from research for:
   - webcam feed: `python .\mediapipe_pose.py --webcam `
   - sourced video: `python .\mediapipe_pose.py .\sauce\<video_file> `

[Folder with testing videos](https://drive.google.com/drive/folders/1sudgYRPLghtPS8Si7gra8Xk_rgEF3Kwk?usp=sharing)