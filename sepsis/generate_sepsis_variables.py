
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

def generate_files():
    df = pd.read_csv('sofa/sofa_respiration.csv')
    df['itemid'] = 0
    df['value'] = df['pf_ratio']
    df.to_csv('feature/PaO2_FiO2.csv', columns=['admissionid','time','itemid','value'],index=False)
    df['value'] = df['pao2']
    df.to_csv('feature/paO2.csv', columns=['admissionid','time','itemid','value'],index=False)
    df['value'] = df['fio2']
    df.to_csv('feature/FiO2_1.csv', columns=['admissionid','time','itemid','value'],index=False)
    df = pd.read_csv('feature/demo.csv')
    df['icustayid'] = df['admissionid']
    df['value']=df['agegroup']
    df.loc[(df['value']=='18-39'), 'value'] = 30
    df.loc[(df['value']=='40-49'), 'value'] = 45
    df.loc[(df['value']=='50-59'), 'value'] = 55
    df.loc[(df['value']=='60-69'), 'value'] = 65
    df.loc[(df['value']=='70-79'), 'value'] = 75
    df.loc[(df['value']=='80+'), 'value'] = 85
    df['age_'] = df['value']
    df.to_csv('feature/age.csv', columns=['icustayid','age_'],index=False)
    df['value']=df['weightgroup']
    df.loc[(df['value']=='59-'), 'value'] = 55
    df.loc[(df['value']=='60-69'), 'value'] = 65
    df.loc[(df['value']=='70-79'), 'value'] = 75
    df.loc[(df['value']=='80-89'), 'value'] = 85
    df.loc[(df['value']=='90-99'), 'value'] = 95
    df.loc[(df['value']=='100-109'), 'value'] = 105
    df.loc[(df['value']=='110+'), 'value'] = 115
    df['Weight_kg_'] = df['value']
    df.to_csv('feature/Weight_kg.csv', columns=['icustayid','Weight_kg_'],index=False)

    df['value']=df['gender']
    df.loc[(df['value']=='Man'), 'value'] = 1
    df.loc[(df['value']!=1), 'value'] = 0
    df['gender_'] = df['value']
    df.to_csv('feature/gender.csv', columns=['icustayid','gender_'],index=False)

    print(df['value'].unique())

def merge_data():
    mimic_head = '''bloc,icustayid,charttime,gender,age,elixhauser,re_admission,died_in_hosp,died_within_48h_of_out_time,mortality_90d,delay_end_of_record_and_discharge_or_death,Weight_kg,GCS,HR,SysBP,MeanBP,DiaBP,RR,SpO2,Temp_C,FiO2_1,Potassium,Sodium,Chloride,Glucose,BUN,Creatinine,Magnesium,Calcium,Ionised_Ca,CO2_mEqL,SGOT,SGPT,Total_bili,Albumin,Hb,WBC_count,Platelets_count,PTT,PT,INR,Arterial_pH,paO2,paCO2,Arterial_BE,Arterial_lactate,HCO3,mechvent,Shock_Index,PaO2_FiO2,median_dose_vaso,max_dose_vaso,input_total,input_4hourly,output_total,output_4hourly,cumulated_balance,SOFA,SIRS'''
    file_list = 'Albumin,Arterial_lactate,Glucose,demo,fluidin,Hb,HR,MeanBP,Potassium,Sodium,SysBP,Total_bili,WBC_count,Arterial_BE,Arterial_pH,Creatinine,DiaBP,GCS,HCO3,Magnesium,Platelets_count,RR,SpO2,Temp_C,FiO2_1,paO2,PaO2_FiO2'
    # file_list = 'FiO2_1,paO2,PaO2_FiO2'
    wf = open('merge.csv', 'w')
    wf.write(mimic_head)
    fs = []
    n_index = len(mimic_head.split(','))
    for file in tqdm(file_list.split(',')):
        if file in mimic_head:
            value_index = mimic_head.split(',').index(file)
            fs.append(file)
            ctime = 0
            for i_line, line in enumerate(open('feature/{:s}.csv'.format(file))):
                if i_line > 2000:
                    # break
                    pass
                if i_line == 0:
                    if line.strip() != 'admissionid,time,itemid,value':
                        print(file, line)
                        break
                else:
                    admissionid,time,itemid,value = line.strip().split(',')
                    new_line = ['1', admissionid, time] + ['' for _ in range(value_index - 3)] + [value]+ ['' for _ in range(n_index - value_index - 1)]
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
    df = pd.read_csv('ast.csv')
    vaso = pd.read_csv('feature/vaso_dose.csv')
    iv = pd.read_csv('feature/iv_dose.csv')
    output = pd.read_csv('feature/output.csv')
    icuids = set(df['icustayid'].unique())
    icuids_vaso = set(vaso['icustayid'].unique())
    icuids_iv = set(iv['icustayid'].unique())
    print('vaso', len(vaso))
    for id in icuids_vaso - icuids:
        vaso = vaso.drop(vaso['icustayid']==id)
        print('vaso', len(vaso))
    print('iv', len(iv))
    for id in icuids_iv - icuids:
        iv = iv.drop(iv['icustayid']==id)
        print('iv', len(iv))

    df = df.set_index(['icustayid','charttime']).join(vaso.set_index(['icustayid','charttime']), on=['icustayid', 'charttime'])
    df = df.join(iv.set_index(['icustayid','charttime']), on=['icustayid', 'charttime'])
    df = df.join(output.set_index(['icustayid','charttime']), on=['icustayid', 'charttime'])
    df['max_dose_vaso'] = df['vaso_dose']
    df['input_4hourly'] = df['iv_dose']
    df['output_4hourly'] = df['output_4h']
    df.to_csv('ast.dose.csv')

def merge_demo():
    df = pd.read_csv('ast.dose.csv')
    gender=pd.read_csv('feature/gender.csv')
    age=pd.read_csv('feature/age.csv')
    weight=pd.read_csv('feature/Weight_kg.csv')
    icuids = set(df['icustayid'].unique())


    df = df.set_index(['icustayid']).join(age.set_index(['icustayid']), on=['icustayid'])
    df = df.join(weight.set_index(['icustayid']), on=['icustayid'])
    df = df.join(gender.set_index(['icustayid']), on=['icustayid'])
    df['age'] = df['age_']
    df['Weight_kg'] = df['Weight_kg_']
    df['gender'] = df['gender_']
    df.to_csv('ast.demo.csv')


def merge_motrality():
    df = pd.read_csv('ast.demo.csv')
    sepsis = pd.read_csv('../concepts/diagnosis/sepsis.csv')
    for id in tqdm(df['icustayid'].unique()):
        line = sepsis.loc[sepsis['admissionid']==id]
        readm = min(1, list(line['admissioncount'])[0] - 1)
        assert readm in [0, 1]
        df.loc[(df['icustayid']==id), 're_admission'] = readm
        dod = list(line['dateofdeath'])[0]
        dd = list(line['dischargedat'])[0]
        ad = list(line['admittedat'])[0]
        if str(dod) == 'nan':
            # print(dod)
            df.loc[(df['icustayid']==id), 'mortality_90d'] = 0
            df.loc[(df['icustayid']==id), 'died_within_48h_of_out_time'] = 0
            df.loc[(df['icustayid']==id), 'died_in_hosp'] = 0
            df.loc[(df['icustayid']==id), 'delay_end_of_record_and_discharge_or_death'] = 0
        else:
            df.loc[(df['icustayid']==id), 'delay_end_of_record_and_discharge_or_death'] = 1
            if dod - dd <= 90 * 24 * 60 * 60 * 1000:
                df.loc[(df['icustayid']==id), 'mortality_90d'] = 1
            else:
                df.loc[(df['icustayid']==id), 'mortality_90d'] = 0
            if dod - dd <= 48 * 60 * 60 * 1000:
                df.loc[(df['icustayid']==id), 'died_within_48h_of_out_time'] = 1
            else:
                df.loc[(df['icustayid']==id), 'died_within_48h_of_out_time'] = 0
            if dod <= dd:
                df.loc[(df['icustayid']==id), 'died_in_hosp'] = 1
            else:
                df.loc[(df['icustayid']==id), 'died_in_hosp'] = 0
    df.to_csv('ast.mort.csv')


def check_null():
    df = pd.read_csv('ast.mort.csv')
    print('Temp_C', df['Temp_C'].mean())
    n = 0
    m = 0
    for c in df.columns:
        data = df[c].unique()
        if len(data) <2:
            print(c)
            n+=1
        else:
            m+=1
    print(m,n)




def main():
    # generate_sofa()
    # generate_sirs()
    # generate_files()
    # return
    # merge_data()
    # sort_data()
    # merge_vaso_iv()
    # merge_demo()
    merge_motrality()
    check_null()



if __name__ == '__main__':
    main()
