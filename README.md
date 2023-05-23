# Medication_name_cleaner
Takes medication lists cleans up and standardizes and also checks the spelling for matches against standard database of medications using fuzzywuzzy. 

This is a medications clean up script for use in databases with free entered medications. It was custom made for Peribank but can be applied to any medications lists. 

Specifically, it standardizes the and cleans up the strings removing comon unhelpful additons such as dosess, punctuation, routes etc. It then makes some common manual fixes as ell as sytematic changes to drug names for common abbreviations. Using a database that is stnadardized and included here, it then matches using fuzzy matches for mispellings in a 3 iteration approach that is successively more aggressive. The script is multiplexed for speed in large databases.
The script outputs dataframe list of cleaned medications, as well as tracked changes to the names at each step to parse for errors. It also calculates the number of uniquemedications to determine the effect of the cleaning. It also outputs a list of the dictionary matches and the frequency of those matches to track for unwanted errors and evaluate whether the data is sufficiently cleaned. Finally it give the  matches themselves and the Levenshtein_ratio, which is default set at a cut off of 85.
For the 3rd itteration, partial matching is used which can be agressive, use with care and review your results. 

For reference. The database is sourced from 
https://www.vumc.org/cpm/medi
Vanderbuilt precision medicine MEDI database.

1. WQ Wei, RM Cronin, H Xu, TA Lasko, L Bastarache, JC Denny, Development and evaluation of an ensemble resource linking medications to their indications, Journal of the American Medical Informatics Association. 2013;20:954-961 doi:10.1136/amiajnl-2012-001431
2. WQ Wei, JD Mosley et al. Validation and Enhancement of a Computable Medication Indication Resource (MEDI) Using a Large Practice-based Dataset. AMIA Annual Symposium, 2013, Washington DC.
