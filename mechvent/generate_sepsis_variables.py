
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
    mimic_head = '''bloc,icustayid,charttime,gender,age,elixhauser,re_admission,died_in_hosp,died_within_48h_of_out_time,mortality_90d,delay_end_of_record_and_discharge_or_death,Weight_kg,GCS,HR,SysBP,MeanBP,DiaBP,RR,SpO2,Temp_C,FiO2_1,Potassium,Sodium,Chloride,Glucose,BUN,Creatinine,Magnesium,Calcium,Ionised_Ca,CO2_mEqL,SGOT,SGPT,Total_bili,Albumin,Hb,WBC_count,Platelets_count,PTT,PT,INR,Arterial_pH,paO2,paCO2,Arterial_BE,Arterial_lactate,HCO3,mechvent,Shock_Index,PaO2_FiO2,median_dose_vaso,max_dose_vaso,input_total,input_4hourly,output_total,output_4hourly,cumulated_balance,SOFA,SIRS,TidalVolume,PEEP'''
    file_list = 'TidalVolume,PEEP,Albumin,Arterial_lactate,Glucose,demo,fluidin,Hb,HR,MeanBP,Potassium,Sodium,SysBP,Total_bili,WBC_count,Arterial_BE,Arterial_pH,Creatinine,DiaBP,GCS,HCO3,Magnesium,Platelets_count,RR,SpO2,Temp_C,FiO2_1,paO2,PaO2_FiO2'
    # mimic_head = '''bloc,icustayid,charttime,FiO2_1'''
    # file_list = 'FiO2_1'
    df = pd.read_csv('feature/mechvent.csv')
    aid_set = set([str(int(x)) for x in df['admissionid'].unique()])
    # file_list = 'FiO2_1,paO2,PaO2_FiO2'
    wf = open('merge.csv', 'w')
    wf.write(mimic_head)
    fs = []
    n_index = len(mimic_head.split(','))
    index_set = set()
    for file in tqdm(file_list.split(',')):
        max_time = 0
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
                    time = str(10 * int(int(time) / 10))
                    key = admissionid + '_' + time + '_'  + file
                    if key in index_set:
                        continue
                    else:
                        index_set.add(key)

                    if admissionid not in aid_set:
                        continue
                    max_time = max(max_time, float(time))
                    new_line = ['1', admissionid, time] + ['' for _ in range(value_index - 3)] + [value]+ ['' for _ in range(n_index - value_index - 1)]
                    # print(n_index, len(new_line))
                    wf.write('\n' + ','.join(new_line))
        else:
            print(file)
        print(file, 'max_time', max_time)
    # print(len(fs))
    wf.close()


def sort_data():
    record_list = []
    df = pd.read_csv('merge.csv')
    data = df['FiO2_1']
    df['charttime'] = (df['charttime'] / 240).astype(int)
    df = df.groupby(['icustayid', 'charttime']).mean()
    data = df['FiO2_1']
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
    df.loc[np.isnan(df['max_dose_vaso']), 'max_dose_vaso'] = 0
    df.loc[np.isnan(df['input_4hourly']), 'input_4hourly'] = 0
    df.loc[np.isnan(df['output_4hourly']), 'output_4hourly'] = 0
    df.to_csv('ast.dose.csv')

def merge_demo():
    df = pd.read_csv('ast.csv')
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
    df.loc[np.isnan(df['age']), 'age'] = df['age'].mean()
    df.loc[np.isnan(df['Weight_kg']), 'Weight_kg'] = df['Weight_kg'].mean()
    df.loc[np.isnan(df['gender']), 'gender'] = 0
    df.to_csv('ast.demo.csv')


def merge_motrality():
    df = pd.read_csv('ast.demo.csv')
    admission= pd.read_csv('../data/admissions.csv')
    for id in tqdm(df['icustayid'].unique()):
        line = admission.loc[admission['admissionid']==id]
        readm = min(1, list(line['admissioncount'])[0] - 1)
        # readm = 0
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

def impute(data):
    isnan = list(np.isnan(data))
    data = list(data)
    first, last = -1, 0
    for i,d in enumerate(data):
        if not isnan[i]:
            if first<0:
                first = i
            last = i
    if first >0:
        for i in range(first):
            data[i] = data[first]
    if last < len(data) -1:
        for i in range(last, len(data)):
            data[i] = data[last]
    isnan = np.isnan(data)
    # print('new-------------', isnan)
    start = 0
    for i,d in enumerate(data):
        if i>0 and isnan[i] and not isnan[i-1]:
            # print('-----------',start)
            start = i
        if start > 0 and isnan[i] and not isnan[i+1]:
            end = i
            # print(start, end, len(data))
            last_value = data[start - 1]
            next_value = data[end + 1]
            for j in range(end+1 - start):
                d = last_value + (next_value - last_value) / (end + 2 - start) * (j + 1)
                # print('----------------', start+j, d)
                data[start + j] = d
            start = len(data)
    return data

def delete_patients_with_high_missing_rate():
    df = pd.read_csv('ast.mort.csv')
    print(len(df['icustayid'].unique()))
    # mechvent = df['mechvent']
    # mechvent[mechvent!=1] = 0
    # df['mechvent'] = mechvent
    cs = set()
    nmiss_count_dict = dict()
    for c in df.columns:
        if len(set(np.isnan(df[c]))) > 1:
            cs.add(c)
    id_list = []
    for id in tqdm(df['icustayid'].unique()):
        nmiss = 0
        for c in cs:
            data = df.loc[(df['icustayid']==id), c]
            if np.isnan(data).min():
                nmiss += 1
        if nmiss < 18:
            id_list.append(id)
        nmiss_count_dict[nmiss] = nmiss_count_dict.get(nmiss, 0)  + 1
    for n in sorted(nmiss_count_dict):
        print(n, nmiss_count_dict[n])

    df = df[df['icustayid'].isin(id_list)]
    print(len(df), len(id_list), len(df['icustayid'].unique()))

    df.to_csv('ast.miss.1.csv')

def generate_action(df):
    setting_th_dict = {
            'TidalVolume': [2.50, 5.00, 7.50, 10.00, 12.50, 15.00],
            'PEEP': [5, 7, 9, 11,13, 15],
            'FiO2_1': [0.3, 0.35, 0.4, 0.45, 0.5, 0.55],
            }
    setting_list =sorted(setting_th_dict.keys())
    for i_s, s in enumerate(setting_list):
        data = df[s]
        data= data[data>=0]
        action = np.zeros_like(data)
        # print(s, len(data))
        # continue
        for i_th, th in enumerate(setting_th_dict[s]):
            action[data > th] = i_th + 1
        for v in range(7):
            print(setting_list[i_s], np.mean(action == v))
        print('  ')
    # print(err)



def proc_missing():
    # print(err)
    df = pd.read_csv('ast.mort.csv')
    df['TidalVolume'] = df['TidalVolume'] / df['Weight_kg']
    # for k in ['PEEP', 'TidalVolume', 'FiO2_1']:
    for k in ['PEEP', 'TidalVolume', 'FiO2_1']:
        data = df[k].values
        data[np.isnan(data)] = 0
        df[k] = data
    # print(err)
    generate_action(df)
    

    print(len(df['icustayid'].unique()))
    # mechvent = df['mechvent']
    # mechvent[mechvent!=1] = 0
    # df['mechvent'] = mechvent
    cs = set()
    for c in df.columns:
        if len(set(np.isnan(df[c]))) > 1:
            print('{:20s}    {:d}%'.format(c, int(np.isnan(df[c]).mean() * 100)))
            cs.add(c)
    for id in tqdm(df['icustayid'].unique()):
        for c in cs:
            data = df.loc[(df['icustayid']==id), c]
            if np.isnan(data).min():
                if id < 10:
                    print(c, list(data))
                df.loc[(df['icustayid']==id), c] = df['icustayid'].mean()
            elif np.isnan(data).max():
                # print(list(data))
                data = impute(data)
                # print(data)
                # print(df.loc[(df['icustayid']==id), pd.Index])
                df.loc[(df['icustayid']==id), c] = data
                data = df.loc[(df['icustayid']==id), c]
                # print(list(data))
                # input()
                # return
    for c in df.columns:
        data = df[c].unique()
        if len(set(np.isnan(data))) > 1:
            print(c, set(np.isnan(data)), np.isnan(data).mean())
        continue
    df.to_csv('ast.miss.csv')


def save():
    df = pd.read_csv('ast.miss.csv')
    head = '''bloc,icustayid,charttime,gender,age,re_admission,died_in_hosp,died_within_48h_of_out_time,mortality_90d,delay_end_of_record_and_discharge_or_death,Weight_kg,GCS,HR,SysBP,MeanBP,DiaBP,RR,SpO2,Temp_C,FiO2_1,Potassium,Sodium,Chloride,Glucose,Creatinine,Magnesium,Total_bili,Albumin,Hb,WBC_count,Platelets_count,Arterial_pH,paO2,Arterial_BE,Arterial_lactate,HCO3,PaO2_FiO2,max_dose_vaso,input_total,input_4hourly,output_total,output_4hourly,TidalVolume,PEEP'''

    id_list = []
    n_c_dict = dict()
    for id in df['icustayid'].unique():
        n = len(df[df['icustayid'] == id])
        n = min(n, 50)
        if n > 5: 
            id_list.append(id)
        n_c_dict[n] = n_c_dict.get(n, 0) + 1
    print('----------------------')
    for n in sorted(n_c_dict.keys()):
        print(n, n_c_dict[n])
    print(len(df['icustayid'].unique()), len(id_list))
    df = df[df['icustayid'].isin(id_list)]
    df.to_csv('ast.left.csv', columns=head.split(','))
    print('feature', len(head.split(',')))


def check_null(file):
    df = pd.read_csv(file)
    n = 0
    m = 0
    for c in df.columns:
        data = df[c].unique()
        if len(set(np.isnan(data))) == 1:
            print(c, set(np.isnan(data)), np.isnan(data).mean())
        continue
        if len(data) <2:
            print(c)
            n+=1
        else:
            m+=1
    print(m,n)

def add_mechvent(csv_file):
    df = pd.read_csv(csv_file)
    id_mechvent_dict = dict()
    for line in open('feature/mechvent.csv'):
        id, t = line.strip().split(',')
        if t != 'time':
            if id not in id_mechvent_dict:
                id_mechvent_dict[id] = set()
            id_mechvent_dict[id].add(int(t))
    value = np.zeros(len(df))
    for i in range(len(df)):
        id = str(int(df.iloc[i]['icustayid']))
        t = int(df.iloc[i]['charttime'])
        assert id in id_mechvent_dict
        if t in id_mechvent_dict[id]:
            mechvent[i] = 1
    df['mechvent'] = mechvent
    df.to_csv(csv_file)





def main():
    # generate_files()
    print('merge_data')
    # merge_data()
    print('sort_data')
    # sort_data()
    print('merge_vaso_iv')
    # merge_vaso_iv()
    print('merge_demo')
    # merge_demo()
    print('merge_motrality')
    # merge_motrality()
    # return
    print('proc_missing')
    # proc_missing()
    print('saving')
    save()
    # check_null('ast.mort.csv')
    # check_null('ast.miss.csv')
    print('check_null')
    # check_null('ast.left.csv')



if __name__ == '__main__':
    main()
