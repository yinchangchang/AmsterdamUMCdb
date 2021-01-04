
#!/usr/bin/env python
# coding=utf-8


import sys

import os
import sys
import time
import numpy as np
import pandas as pd
from sklearn import metrics
import random
import json
from glob import glob
from collections import OrderedDict
from tqdm import tqdm


def merge_data():
    mimic_head = '''bloc,icustayid,charttime,gender,age,elixhauser,re_admission,died_in_hosp,died_within_48h_of_out_time,mortality_90d,delay_end_of_record_and_discharge_or_death,Weight_kg,GCS,HR,SysBP,MeanBP,DiaBP,RR,SpO2,Temp_C,FiO2_1,Potassium,Sodium,Chloride,Glucose,BUN,Creatinine,Magnesium,Calcium,Ionised_Ca,CO2_mEqL,SGOT,SGPT,Total_bili,Albumin,Hb,WBC_count,Platelets_count,PTT,PT,INR,Arterial_pH,paO2,paCO2,Arterial_BE,Arterial_lactate,HCO3,mechvent,Shock_Index,PaO2_FiO2,median_dose_vaso,max_dose_vaso,input_total,input_4hourly,output_total,output_4hourly,cumulated_balance,SOFA,SIRS'''
    file_list = 'Albumin,Arterial_lactate,Glucose,demo,fluidin,Hb,HR,MeanBP,Potassium,Sodium,SysBP,Total_bili,WBC_count,Arterial_BE,Arterial_pH,Creatinine,DiaBP,GCS,HCO3,Magnesium,Platelets_count,RR,SpO2,Temp_C'
    wf = open('merge.csv', 'w')
    wf.write(mimic_head)
    fs = []
    n_index = len(mimic_head.split(','))
    for file in file_list.split(','):
        if file in mimic_head:
            value_index = mimic_head.split(',').index(file)
            fs.append(file)
            ctime = 0
            for i_line, line in enumerate(open('feature/{:s}.csv'.format(file))):
                if i_line > 20:
                    break
                if i_line == 0:
                    if line.strip() != 'admissionid,time,itemid,value':
                        break
                else:
                    admissionid,time,itemid,value = line.strip().split(',')
                    new_line = ['1', admissionid, time] + ['' for _ in range(value_index - 4)] + [value]+ ['' for _ in range(n_index - value_index)]
                    # print(n_index, len(new_line))
                    wf.write('\n' + ','.join(new_line))
        else:
            print(file)
    # print(len(fs))
    wf.close()


def sort_data():
    record_list = []
    df = pd.read_csv('merge.csv')
    df['charttime'] = (df['charttime'] / 240).astype(int)
    df = df.groupby(['icustayid', 'charttime']).mean()
    df.to_csv('ast.csv')

def merge_vaso_iv():
    vaso = pd.read_csv('feature/vaso.csv')
    wgs = vaso['weightgroup'].unique()
    for wg in wgs:
        if type(wg) is float:
            print(wg)
            continue
        if wg == None or len(wg.strip()) == 0:
            continue
        elif '59-' == wg:
            print(len(wg), len(wg.strip()), wg)
            nwg = 55
        elif '110+' == wg:
            print(len(wg), len(wg.strip()), wg)
            nwg = 115
        else:
            print(len(wg), len(wg.strip()), wg)
            minw,maxw = wg.split('-')
            nwg = int((int(minw) +  int(maxw) + 1)/2)
        vaso.loc[(vaso['weightgroup']==wg), 'weightgroup'] = nwg
    vaso['charttime'] = (vaso['charttime'] / 240).astype(int)
    vaso.to_csv('tmp.csv')



def main():
    # generate_sofa()
    # generate_sirs()
    # merge_data()
    # sort_data()
    merge_vaso_iv()



if __name__ == '__main__':
    main()
