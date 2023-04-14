# This sript cleans a list of peribank medications for spelling and consistancy
# It outputs the orgional spelling and a series of fixes 
# Last updated 13 April 2023, Maxim Seferovic (seferovi@bcm.edu) & Brandon T. Garcia (Brandon.Garcia@bcm.edu
# !/usr/bin/env python3


import re
import pandas as pd
import pickle
import math
from collections import defaultdict
from rapidfuzz import fuzz
from multiprocessing import Pool, cpu_count
num_processes = cpu_count()


def get_medications(): 
    with open("Ensemble_meds.pkl", "rb") as f:
        return pickle.load(f)

def get_words(): 
    with open("Ensemble_words.pkl", "rb") as f:
        return pickle.load(f)

def combine_dicts(dicts):
    merged_dict = {}
    for dict in dicts:
        for key in dict:
            if key in merged_dict:
                merged_dict[key].extend(dict[key])
            else:
                merged_dict[key] = dict[key].copy() 
    for key in merged_dict:
        string_counts = {}
        for string in merged_dict[key]:
            if string not in string_counts:
                string_counts[string] = 1
            else:
                string_counts[string] += 1
        list = [(f"{string},{count}") for string, count in string_counts.items()]
        merged_dict[key] = list
    return merged_dict

def save_dict(dictionary): 
    with open ("Dictionary_matches.csv", 'w') as f: 
        f.write ("Medication, Matches\n")
        for k,v in dictionary.items():
            f.write (k + ',\"' + ','.join(v) + '\"\n')

def keep_a2z(string):
    string = string.replace('-',' ').lower()
    pattern = r'(?<!b)\d'
    string = re.sub(pattern, '', string)
    pattern = r'[^a-zA-Z0-9\s]'
    return re.sub(pattern, '', string)

def remove_excessive_whitespace(string):
    return (' '.join(string.split())).strip()

def strip_terms(string, things_to_strip): 
    for ending in things_to_strip:
        if string.endswith(ending):
            string = string[: -len(ending)].strip()
    return string
    
def word_strip(series): 
    things_to_strip = [' ', '/t', ' crm', ' cream', ' vaginal', ' vag', ' top', ' sq', ' topical', 
        ' po', ' odt', ' tab', ' pm', ' extra',  ' inhaler', ' jelly', ' xl', ' plus',
        ' mg', ' soln', ' ml', ' flush', ' tab', ' mcg', ' pf', ' id', ' in', ' premix', ' pot',  
        ' continous', ' infusion', ' cap',' bolus', ' gel', ' patch', ' sodium', ' injec',
        ' inh', ' neb', ' or', ' ophthalmic', ' ointment', ' hbr', ' tabs', ' lr', ' multi', 
        ' ivpb', ' drip', ' ac', ' acet', ' in', ' g', ' id', ' sol', ' sal', ' push', ' vac',
        ' buffered', ' nacl', ' ivpb', ' cq', ' gram', ' epidural infursion', ' infus', ' suppository',
        ' oral', ' dm', ' hfa', ' x', ' iv', ' tablet', ' hci', ' topical', ' hcl', ' w', 
        ' lotion', ' pack', ' nasal',' drops',' strength',' pf',' inj',' inhaler', ' inf',
        ' bid', 'regular', ' nasal', ' spray', ' micronized', ' injections', ' hc',
        ' solution', ' suspension', ' otic', ' ear', ' assure', ' dha']
    while True: #strip iteratively in case multiple/stacked instances.  
        prev_series = series
        series = strip_terms(series, things_to_strip)
        if series == prev_series: break
    series = remove_excessive_whitespace(series)
    return series

def manual_edits(df): # modifies the data itself
    things_to_fix = (('pnv','prenatal vitamin'), ('mag sulfate','magnesium sulfate'), 
        ('asa','acetylsalicylic acid'),('ancef','cefazolin'), ('aspirin','acetylsalicylic acid'),
        ('ohp','hydroxyprogesterone caproate'),('ohp caproate','hydroxyprogesterone caproate'), 
        ('glucophage','metformin'), ('pnc','penicillin')) 
    for item in things_to_fix: 
        df.replace(item[0], item[1], inplace=True)
    return df

def save_changes(spelling_changes): 
    spelling_changes = list(set(spelling_changes)) # removes redundancy
    spelling_changes.sort(key=lambda x: float(x.split(',')[2]), reverse=True) #sorts by score
    spelling_changes.insert(0, 'matched,replaced,Levenshtein_ratio,partial_match')
    with open ("Drug_spelling_matches.csv", 'w') as f: 
        f.write("\n".join(spelling_changes))   
 
def manual_curation(match_list): # modifies the match dictionaries
    #These are fixes for replacements that were problomatic after manual review of "Drug_spelling_matches.csv"
    match_list.extend(["vaseline", "prenatal vitamin"])
    manual_interventions = (("inulin","insulin"),("penicillin g","penicillin"))
    for item in manual_interventions:
        while item[0] in match_list:
            match_list = [item[1] if x == item[0] else x for x in match_list]
    return tuple(match_list)
  
def fuzzy_replace_meds(chunk, threshold=80):   
    spelling_changes = []
    dictionary_of_changes = defaultdict(list)
    
    def replace_with_best_match(cell, match_list, partial):
            best_score = threshold
            best_match = cell
            for x in match_list:
                if partial == True:
                    if len(cell) < 4 : continue 
                    score = fuzz.partial_ratio(cell,x)
                else: 
                    score = fuzz.ratio(cell, x)
                if score >= best_score:
                    best_score = score
                    best_match = x
                 
            if best_match != cell: 
                dictionary_of_changes[best_match].append(cell)
                spelling_changes.append(f"{best_match},{cell},{best_score},{partial}")
            return best_match
    
    #Iterations 1/3, match to medication
    medications = manual_curation(get_medications())
    temp_df = chunk.str.split(',', expand=True)
    for col in temp_df.columns:   
        temp_df[col] = temp_df[col].apply(replace_with_best_match, args=(medications, False))
    temp_series_values = temp_df.apply(lambda x: ','.join(y for y in x.astype(str) if y != 'None' and pd.notna(y)), axis=1)
    temp_series = pd.Series(temp_series_values.values, index=chunk.index, name=chunk.name)
    
    #Iterations 2/3, match to words after spitting to words
    words = manual_curation(get_words())   
    temp_df = temp_series.str.replace(",", " _COMMA_ ").str.split(' ', expand=True)
    for col in temp_df.columns:   
        temp_df[col] = temp_df[col].apply(replace_with_best_match, args=(words, False))
    temp_series_values = temp_df.apply(lambda x: ' '.join(y for y in x.astype(str) if y != 'None' and pd.notna(y)), axis=1)
    temp_series_values = temp_series_values.str.replace(" _COMMA_ ", ",")
    temp_series = pd.Series(temp_series_values.values, index=chunk.index, name=chunk.name)
    
    #Iterations 3/3, PARTIAL match to medications
    #Modded. This is very aggressive, recoded for only specific medications where called for rather than whole med list
    meds_for_partial_match = ("insulin", "fentanyl")
    temp_df = temp_series.str.split(',', expand=True)
    for col in temp_df.columns:   
        temp_df[col] = temp_df[col].apply(replace_with_best_match, args=(meds_for_partial_match, True))
    temp_series_values = temp_df.apply(lambda x: ','.join(y for y in x.astype(str) if y != 'None' and pd.notna(y)), axis=1)
    temp_series = pd.Series(temp_series_values.values, index=chunk.index, name=chunk.name)
    
    return temp_series, spelling_changes, dictionary_of_changes
 
def split_series(series):
    chunk_size = math.ceil(len(series) / num_processes) # math.ceil just rounds up so no fraction
    return [series[i:i + chunk_size] for i in range(0, len(series), chunk_size)]

def apply_multiprocess(df):
    spelling_changes = []
    list_of_dictionaries = []
    with Pool(processes=num_processes) as pool:
        chunks = split_series(df['word_striped'])
        processed_chunks_and_counts = pool.map(fuzzy_replace_meds, chunks)
        processed_chunks = [chunk for chunk, _, _ in processed_chunks_and_counts]
        for changes in (changes for _, changes, _ in processed_chunks_and_counts):
            spelling_changes.extend(changes)
        list_of_dictionaries = [dictionary for _, _, dictionary in processed_chunks_and_counts]
        
    dictionary = combine_dicts(list_of_dictionaries)
    df['spelling'] = pd.concat(processed_chunks)
    save_changes(spelling_changes)
    
    return df, dictionary
 
def enumerate_unique(df):
    for col in df.columns: 
        unique = df[col].nunique()
        new_name = (f"{col} ({unique} unique)")
        df = df.rename(columns={col : new_name})
    return df
    
def main(): 
    # Had to clean this up as the file contains commas that are messing with Pandas
    with open ('unique_values.txt', 'r') as f: 
        medications_list = f.read()  
    meds = medications_list.splitlines() 
    final_meds = [i.strip() for sublist in meds for i in sublist.split(',') if i.strip()]           
    df = pd.DataFrame(final_meds, columns=['PBDB_entry'])
    df['alphabet_filtered'] = df['PBDB_entry'].apply(keep_a2z)
    df['word_striped'] = df['alphabet_filtered'].apply(word_strip)
    df, dictionary = apply_multiprocess(df)  
    save_dict(dictionary)
    df = enumerate_unique(df)
    df.to_csv("Cleaned_medications.csv", index=False)
    
if __name__ == '__main__': 
    main()