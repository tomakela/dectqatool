# dectqatool: Dual Energy CT QA Tool
## Introduction
### Dual Energy CT
Dual Energy Computed Tomography (DECT) utilizes multiple X-ray tube voltages in forming the images, by utilizing differing attenuation properties, and therefore contrasts, between the two energy spectrums. In addition to normal image reconstruction with kernel and other parameters, DECT includes additional post-processing steps such as material decomposition, or virtual monoenergetic or non-contrast images. Comprehensive DECT quality assurance (QA) includes both traditional CT instrumentation monitorin (such as radiation measurements and HU consistency), but also the subsequent processing steps taken by (possibly external) reconstruction and analysis software.
### Tool for DECT Phantom
This tools aims to make offline analysis of DECT images acquired from Multi-Energy CT Phantom by Sun Nuclear (https://www.sunnuclear.com/products/multi-energy-ct-phantom) easy. The phantom contains inserts with various elemental compositions, such as various calcium and iodine targets. Some pointing&clicking is still required. It is a modification to 3D Slicer (https://www.slicer.org/): the code adds a toolbar, i.e. it is not a module(!), meant to be clicked through by the user. This is mainly because the suggested workflow uses standard modules for control point modifications and calculating statistics. Tested on 3D Slicer 5.0.2 (and newer)
![image](https://user-images.githubusercontent.com/9822663/229784606-1fb08dd0-60b2-4476-9c19-31c602af9736.png)

## Basic usage
### Installation
To add the Toolbar copy *.slicer.rc* to your home folder. In Windows something like c:\users\username and in Linux/MacOS something like /home/username, or point to it in 3D Slicer *Edit>Application Settings>General>Application startup script* (you might like to rename the file as non-hidden)

Note: you can also copy-paste the file contents to 3D Slicer python interactor (View>Python Interactor or ctrl+3)
### Steps
Load your data to 3D Slicer. If opening multiple DICOM files fails, it is advised to use *Add DICOM Data* module. Make sure you are not loading the data as MultiVolume! This can happen, if you load multiple series from the same study. So.. Add DICOM data>Advanced>Examine>Select Scalar volume reader>Load:
![image](https://user-images.githubusercontent.com/9822663/229774002-591338f8-9a55-4130-8cb8-9d20a4a63943.png)

We assume that you have imaged the phantom in normal position. Using gantry tilt will most likely make the software to fail. **All the magic happens in the Red Slice view**. Set it to axial.

**1) Loc. phantom** tries to detect the high contrast fiducials in the phantom middle. If it doesn't work, move to the correct slice manually. Preferrably use base images (normal CT images) for this, i.e. active background volume in Red view
![image](https://user-images.githubusercontent.com/9822663/221784632-3da6419e-d8eb-4b14-b9c1-f2a702eac705.png)  
**2) Move -35 mm** (and **5) Move +70 mm**) translates the Red View accordingly  
**3) Detect inserts** gives you fiducials based on where the inserst should be. You might want to change the code e.g. if your s-insert is somewhere else.  
![image](https://user-images.githubusercontent.com/9822663/221786466-3ab0b9fd-c777-48e0-9727-278130e07d62.png)  
You can easily fix small rotation errors in the Transforms-module  
![image](https://user-images.githubusercontent.com/9822663/221786160-a1cac438-8025-432a-a2eb-e26d4a0c45e7.png)
- Only use Rotation>IS (and translations in LR and PA if needed)
- Don't edit transforms starting with double underscore. They are there to make rotations consistent and center of rotation the center fiducial
- You can transform the whole phantom, the middle segment ("Head phantom"), the s-insert, or body part separately
- You can also drag the fiducials as needed for the first slice  

**4) Draw to label** creates ROIs for the current slice
- **YOU CAN CHANGE THE ROI/VOI RADIUS IN THE MARKUP MODULE** by editing the description  
![image](https://user-images.githubusercontent.com/9822663/221791227-a9204724-74f1-43c4-9f83-24fcb39b14db.png)  
- You can redo the current ROI if needed (drag fiducials etc)  
![image](https://user-images.githubusercontent.com/9822663/221787438-84cec664-6ee5-48be-8534-61f08c861a90.png) -> Edit body_tf -> 4) Draw to label ->
![image](https://user-images.githubusercontent.com/9822663/221787531-de47e157-7769-4e85-92d7-349d70f63153.png)  

**5) Move to +70mm** or whatever is your last slice, **4) Draw to label**, and finally press **6) Interpolate** to create the final VOI
You can again move the fiducials as you create your second ROI  
![image](https://user-images.githubusercontent.com/9822663/221788702-2b1dccf4-6b35-4471-8316-8c051fc8fbde.png)
![image](https://user-images.githubusercontent.com/9822663/221788759-f986cf55-e744-4926-8e1b-9c32092449aa.png)

  
**7) Label to segm** converts your label map to segmentation to be used with Segmentation statistics -module
- **You can now use the same segmentation for other volumes from the same acquistion (geometry), such as exported DECT parametric maps**
- Segmentation statistics does resampling for you
- Suggested settings:  
![image](https://user-images.githubusercontent.com/9822663/221789861-cd4c1fd4-eb15-43cc-8d63-22d882c1a86e.png)  

The table can be saved as tab- or comma-separated or .txt
  
![image](https://user-images.githubusercontent.com/9822663/221789659-8fb3d39f-db63-490a-9a51-ac7ce54013e0.png)

### Known bugs and TO-DO
- Add sample data
- Comment the code
## Disclaimer
No warranties express or implied. The code might require modifications for your specific use cases.
