# content-based-audio-retrieval
A simple **Python** based application which demonstrates the use of **Flask** + **LibRosa** + **HTML** + **CSS** + **Javascript** + **MongoDB** in a single application. 


It provides content based audio retrieval. A user can upload .mp3 file as an audio query. MFCC of uploaded .mp3 file is calculated and difference of MFCC is calculated to compare it with the audio collection available in the system. The search results are shown on searchresults.html


At the first place, you need to build your audio collection (.mp3 files) which need to be placed in `/static/audios/`. `/collection` caclculates the MFCC and waveform for each of these .mp3 files and stores the .png files for each MFCC and waveform in `/static/waves`. The acutal value of MFCC along with other information for each file is stored in database (mongodb) which is retrieved during the matching phase.
