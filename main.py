import json
from statistics import mean
from pyvis.network import Network
import math

net = Network(height="1500px",width="100%",bgcolor="#222222",font_color="white")
net.barnes_hut()
net.repulsion(node_distance=300, spring_length=400)

graph_name = 'network_graph.html'

min_weight_ratio = 0.6
min_vis_weight = 1
max_vis_weight = 10

frame_length_weight = 2 # frame length

frame_delta_weight = 0.2 # duration between frames
frame_delta_thresh = 0.001 # max difference between durations

signal_weight = 0.2 # signal strength
signal_thresh = 1 # max signal strength difference (dB)

destination_weight = 1 # destination mac
ssid_weight = 5 # ssid requested
sr_weight = 2.5 # supported rates
ch_weight = 1 # current channel
esr_weight = 1.5 # extended supported rates
rmcap_weight = 1 # Radio Management(RM) capabilities
ht_weight = 1 # High Throughput(HT) Capabilities Info 
htamp_weight = 0.5 # HT A-MPDU Parameters
htmcs_weight = 0.5 # Rx Supported Modulation and Coding Scheme Set
iant_weight = 0.5 # Access Network Type
ii_weight = 0.5 # Internet
ia_weight = 0.5 # ASRA
iu_weight = 0.5 # UESA
ih_weight = 0.5 # HESSID
vhtc_weight = 1.5 # Very High Throughput(VHT) Capabilities Info    
vhtrxmcs_weight = 0.5 # Rx Modulation and Coding Scheme(MCS) Map  
vhtrxh_weight = 0.5 # Rx Highest Long GI Data Rate (in Mb/s)
vhtrxnst_weight = 0.5 # Max NSTS Total  
vhttxmcs_weight = 0.5 # Tx MCS Map
vhttxh_weight = 0.5 # Tx Highest Long GI Data Rate (in Mb/s)
vhtext_weight = 0.5 # Extended NSS BW Capable Boolea
vhtres_weight = 0.5 # Reserved
s1c_weight = 0.5 # Sub 1GHz RAW Control  
s1d_weight = 0.5 # Sub 1GHz RAW Slot Definition  
s1s_weight = 0.5 # Start Time Indication
s1i_weight = 0.5 # Channel Indication   
oui_weight = 2 # Organizational Unique Identifier
ouit_weight = 0.5 # Vendor Specific OUI Type 
ie_weight = 0.5 # Information Element Type 
he_weight = 0.5 # HE MAC Capabilities Information
device_weight = 1 # Device and Vendor Information
ext_info_weight = 0.5 # Extra tag Information


def dict_raise_on_duplicates(ordered_pairs):
    d = {}
    for k, v in ordered_pairs:
        if k in d:
            if type(d[k]) is list:
                d[k].append(v)
            else:
                d[k] = [d[k],v]
        else:
            d[k] = v
    return d

def filter_vars(tag,num):
    try:
        return [elem[tag] for elem in mgt_tags if elem['wlan.tag.number']==num][0]
    except:
        return []
def filter_multi(header,tag,num):
    try:
        return [elem[header][tag] for elem in mgt_tags if elem['wlan.tag.number']==num][0]
    except:
        return []
def ext_vars(tag,num):
    try:
        return [elem[tag] for elem in mgt_ext_tags if elem['wlan.ext_tag.number']==num][0]
    except:
        return []
def ext_multi(header,tag,num):
    try:
        return [elem[header][tag] for elem in mgt_ext_tags if elem['wlan.ext_tag.number']==num][0]
    except:
        return []

def create_matcher(criterea,weight,min_thresh,filters):
    edges = dict()
    users_seen = dict()
    for user in merged_users:
        users_seen[user] = set()
    for user in merged_users:
        user_des = [elem for elem in merged_users[user][criterea] if elem not in filters]
        if user_des==[]:continue
        for neighbor in merged_users:
            if neighbor==user:continue
            neighbor_des = [elem for elem in merged_users[neighbor][criterea] if elem not in filters]
            if neighbor_des==[]:continue
            if neighbor in users_seen[user]:continue
            if user in users_seen[neighbor]:continue
            n_matching = len(set(user_des).intersection(set(neighbor_des)))
            if n_matching>min_thresh:
                if user not in edges:
                    edges[user] = dict()
                edges[user][neighbor] = weight*n_matching    
                users_seen[user].add(neighbor)
                users_seen[neighbor].add(user)
    return edges

# with open('Collected_Data/anon.json','r') as f:
with open('anon.json','r') as f:
    data = f.read()

parsed_data = json.loads(data, object_pairs_hook=dict_raise_on_duplicates) 

filtered_packets = [elem for elem in parsed_data if 'wlan' in elem['_source']['layers']]
filtered_packets = [elem for elem in filtered_packets if 'wlan.mgt' in elem['_source']['layers']]
filtered_packets = [elem for elem in filtered_packets if 'wlan.fc.type_subtype' in elem['_source']['layers']['wlan']]
filtered_packets = [elem for elem in filtered_packets if elem['_source']['layers']['wlan']['wlan.fc.type_subtype']=='0x0004']
filtered_packets = [elem for elem in filtered_packets if len(elem['_source']['layers']['wlan.mgt']['wlan.tagged.all'])>0]
filtered_packets = [elem for elem in filtered_packets if 'wlan.ta_resolved' in elem['_source']['layers']['wlan']]


    
all_mgt_tags = dict()
cleaned_users = []
device_filters = set()
ext_filters = set()
for frame in filtered_packets:
    cleaned_user = dict()
    cleaned_user['frame_time'] = float(frame['_source']['layers']['frame']['frame.time_epoch'])
    cleaned_user['frame_time_delta'] = float(frame['_source']['layers']['frame']['frame.time_delta'])
    cleaned_user['frame_time_delta_displayed'] = float(frame['_source']['layers']['frame']['frame.time_delta_displayed'])
    cleaned_user['frame_length'] = float(frame['_source']['layers']['frame']['frame.len'])
    
    # extract radiotap features
    cleaned_user['signal_strength'] = int(frame['_source']['layers']['radiotap']['radiotap.dbm_antsignal'])

    # extract wlan features
    cleaned_user['source_mac'] = frame['_source']['layers']['wlan']['wlan.sa']
    cleaned_user['source_mac_resolved'] = frame['_source']['layers']['wlan']['wlan.sa_resolved']
    cleaned_user['destination_mac'] = frame['_source']['layers']['wlan']['wlan.da']
    cleaned_user['destination_mac_resolved'] = frame['_source']['layers']['wlan']['wlan.da_resolved']
    cleaned_user['sequence_number'] = frame['_source']['layers']['wlan']['wlan.seq']

    # extract wlan management features
    mgt_tags = frame['_source']['layers']['wlan.mgt']['wlan.tagged.all']['wlan.tag']
    
    # count wlan management tags frequency
    for tag in mgt_tags:
        if tag['wlan.tag.number'] in all_mgt_tags:
            all_mgt_tags[tag['wlan.tag.number']] += 1
        else:
            all_mgt_tags[tag['wlan.tag.number']] = 1
    
    # initialize user
    cleaned_user['all_tags'] = []
    # tag number 0
    try:
        cleaned_user['ssid'] = [elem['wlan.ssid'] for elem in mgt_tags if elem['wlan.tag.number']=='0'][0]
        if not cleaned_user['ssid'].replace(' ','').replace('-','').isalnum():
            cleaned_user['ssid'] = [elem['wlan.ssid_raw'] for elem in mgt_tags if elem['wlan.tag.number']=='0'][0][0]
            if len(cleaned_user['ssid'])>14: cleaned_user['ssid'] = ''
    except:
        cleaned_user['ssid'] = ''
    if cleaned_user['ssid'] != '':cleaned_user['all_tags'].append('0')
    
    # tag number 1
    cleaned_user['supported_rates']=filter_vars('wlan.supported_rates','1')
    if len(cleaned_user['supported_rates'])>0:cleaned_user['all_tags'].append('1')
        
    # tag number 3
    cleaned_user['current_channel']=filter_vars('wlan.ds.current_channel','3')
    if len(cleaned_user['current_channel'])>0:cleaned_user['all_tags'].append('3')
    
    # tag number 45
    cleaned_user['ht_capabilities']=filter_vars('wlan.ht.capabilities','45')
    cleaned_user['ht_ampduparam']=filter_vars('wlan.ht.ampduparam','45')
    try:
        cleaned_user['ht_mcsset'] = [elem['wlan.ht.mcsset']['wlan.ht.mcsset.rxbitmask_raw'][0] for elem in mgt_tags if elem['wlan.tag.number']=='45'][0]
    except:
        cleaned_user['ht_mcsset'] = []
        
    if len([elem for elem in mgt_tags if elem['wlan.tag.number']=='45'])>0:cleaned_user['all_tags'].append('45')
    
    # tag number 50
    cleaned_user['extended_supported_rates']=filter_vars('wlan.extended_supported_rates','50')
    if len(cleaned_user['extended_supported_rates'])>0:cleaned_user['all_tags'].append('50')
    
    # tag number 70
    cleaned_user['rmcap']=filter_vars('wlan.rmcap','70')
    if len(cleaned_user['rmcap'])>0:cleaned_user['all_tags'].append('70')
    
    # tag number 107
    cleaned_user['interworking_access_network_type'] = filter_vars('wlan.interworking.access_network_type','107')
    cleaned_user['interworking_internet'] = filter_vars('wlan.interworking.internet','107')
    cleaned_user['interworking_asra'] = filter_vars('wlan.interworking.asra','107')
    cleaned_user['interworking_uesa'] = filter_vars('wlan.interworking.uesa','107')
    cleaned_user['interworking_hessid'] = filter_vars('wlan.interworking.hessid','107')        
    if len([elem for elem in mgt_tags if elem['wlan.tag.number']=='107'])>0:cleaned_user['all_tags'].append('107')
    
    # tag number 127
    cleaned_user['extcap'] = filter_vars('wlan.extcap','127')
    if len(cleaned_user['extcap'])>0:cleaned_user['all_tags'].append('127')
    
    # tag number 191
    cleaned_user['vht_capabilities'] = filter_vars('wlan.vht.capabilities','191')
    cleaned_user['vht_mcsset_rxmcsmap'] =filter_multi('wlan.vht.mcsset','wlan.vht.mcsset.rxmcsmap','191')
    cleaned_user['vht_mcsset_rxhighestlonggirate'] = filter_multi('wlan.vht.mcsset','wlan.vht.mcsset.rxhighestlonggirate','191')
    cleaned_user['vht_mcsset_max_nsts_total'] = filter_multi('wlan.vht.mcsset','wlan.vht.mcsset.max_nsts_total','191')
    cleaned_user['vht_mcsset_txmcsmap'] = filter_multi('wlan.vht.mcsset','wlan.vht.mcsset.txmcsmap','191')
    cleaned_user['vht_mcsset_txhighestlonggirate'] = filter_multi('wlan.vht.mcsset','wlan.vht.mcsset.txhighestlonggirate','191')
    cleaned_user['vht_mcsset_ext_nss_bw_cap'] =filter_multi('wlan.vht.ncsset','wlan.vht.ncsset.ext_nss_bw_cap','191')
    cleaned_user['vht_mcsset_reserved'] =filter_multi('wlan.vht.ncsset','wlan.vht.ncsset.reserved','191')
        
    if len([elem for elem in mgt_tags if elem['wlan.tag.number']=='191'])>0:cleaned_user['all_tags'].append('191')
    
    # tag number 208
    cleaned_user['s1g_control'] = filter_vars('wlan.s1g.rps.raw_control','208')
    cleaned_user['s1g_slot_definition'] =filter_vars('wlan.s1g.rps.raw_slot_definition','208')
    cleaned_user['s1g_slot_definition.start_time'] = filter_vars('wlan.s1g.raw_slot_definition.raw_start_time','208')
    cleaned_user['s1g_channel_indication'] = filter_vars('wlan.s1g.rps.channel_indication','208')
    
    if len([elem for elem in mgt_tags if elem['wlan.tag.number']=='208'])>0:cleaned_user['all_tags'].append('208')
    
    # tag number 221
    cleaned_user['oui'] = filter_vars('wlan.tag.oui','221')
    cleaned_user['oui_type'] = filter_vars('wlan.vendor.oui.type','221')
    cleaned_user['ie_type'] = filter_vars('wlan.wfa.ie.type','221')
    tag_frame = [elem for elem in mgt_tags if elem['wlan.tag.number']=='221']
    if len(tag_frame)>0:
        tag_frame = tag_frame[0]
        cleaned_user['all_tags'].append('208')
        for key in tag_frame:
            if ':' not in key:continue
            k,v = key.split(': ')
            if '(' in v:
                v = v.split('(')[-1][:-1]
            if len(v.replace(' ',''))==0:continue 
            cleaned_user[k] = v
            device_filters.add(k)
    
    # extended tag number 255 ext_tag number 35
    if 'wlan.ext_tag' not in frame['_source']['layers']['wlan.mgt']['wlan.tagged.all']:
        cleaned_users.append(cleaned_user)
        continue
    mgt_ext_tags = frame['_source']['layers']['wlan.mgt']['wlan.tagged.all']['wlan.ext_tag']
    if 'wlan.ext_tag.number' in mgt_ext_tags:
        mgt_ext_tags = [mgt_ext_tags]
    cleaned_user['he_mac_caps'] = ext_vars('wlan.ext_tag.he_mac_caps','35')
    ext_tag_frame = [elem for elem in mgt_ext_tags if elem['wlan.ext_tag.number']=='35']
    if len(cleaned_user['he_mac_caps'])>0:
        ext_tag_frame = ext_tag_frame[0]
        cleaned_user['all_tags'].append('ext_35')
        for key in ext_tag_frame:
            if 'wlan' in key:continue
            for subkey in ext_tag_frame[key]:
                if 'raw' in subkey:continue
                if 'tree' in subkey:continue
                filtered_key = '_'.join(subkey.split('.')[-2:])
                if '.' in subkey:
                    cleaned_user[filtered_key] = ext_tag_frame[key][subkey]
                    ext_filters.add(filtered_key)
                else:
                    for subsubkey in ext_tag_frame[key][subkey]:
                        if 'raw' in subsubkey:continue
                        if 'tree' in subsubkey:continue
                        if ':' in subsubkey:
                            k,v = subsubkey.split(': ')
                            cleaned_user[k]=v
                            ext_filters.add(k)
                        else:
                            filtered_key = '_'.join(subsubkey.split('.')[-2:])
                            cleaned_user[filtered_key] = ext_tag_frame[key][subkey][subsubkey]
                            ext_filters.add(filtered_key)
    cleaned_users.append(cleaned_user)

# Pad keys
all_keys = set()
for user in cleaned_users:
    for key in user:
        all_keys.add(key)
for i,user in enumerate(cleaned_users):
    for key in all_keys:
        if key in user:continue
        cleaned_users[i][key] = []

with open('parsed_data/cleaned.txt','w+') as f:
    for user in cleaned_users:
        f.writelines(str(user)+'\n')

all_macs = set()
for user in cleaned_users:
    all_macs.add(user['source_mac_resolved'])
intermediate_users = dict()
for unique_mac in all_macs:
    intermediate_users[unique_mac] = [elem for elem in cleaned_users if elem['source_mac_resolved']==unique_mac]
with open('parsed_data/intermediate.txt','w+') as f:
    for user in intermediate_users:
        f.writelines(user+': \n')
        for elem in intermediate_users[user]:
            f.writelines(str(elem)+'\n')
        f.write('\n')


merged_users = dict()
unique_skips = ['frame_time','frame_time_delta','frame_time_delta_displayed','sequence_number']
for user in list(intermediate_users):
    merged_users[user] = dict()
    for key in all_keys:
        merged_users[user][key] = []
        vals = [elem[key] for elem in intermediate_users[user] if elem[key]!='']
        merged_vals = set()
        for i,elem in enumerate(vals):
            if elem ==[]:continue
            if isinstance(elem,list):
                for subelem in elem:
                    merged_vals.add(subelem)
            else:
                merged_vals.add(elem)
        merged_users[user][key] = list(merged_vals)

with open('parsed_data/merged.json','w+') as f:
    json.dump(merged_users,f)

filter_headers=['frame','antenna','wlan','wlan_management','HT_info','Interworking_info','VHT_info','Sub_1GHz_Control','Device_info','Ext_tag']
filters_tags = [['frame_length','frame_time_delta'],
                ['signal_strength'],
                ['destination_mac_resolved'],
                ['ssid','supported_rates','current_channel',
                 'extended_supported_rates','rmcap'],
                ['ht_capabilities','ht_ampduparam','ht_mcsset'],
                ['interworking_access_network_type','interworking_internet','interworking_asra',
                 'interworking_uesa','interworking_hessid'],
                ['vht_capabilities','vht_mcsset_rxmcsmap','vht_mcsset_rxhighestlonggirate',
                 'vht_mcsset_max_nsts_total','vht_mcsset_txmcsmap',
                 'vht_mcsset_txhighestlonggirate','vht_mcsset_ext_nss_bw_cap','vht_mcsset_reserved'],
                ['s1g_control','s1g_slot_definition','s1g_slot_definition.start_time','s1g_channel_indication'],
                ['oui','oui_type','ie_type']+list(device_filters),
                ['he_mac_caps']+list(ext_filters)
               ]

frame_length_edges = dict()
users_seen = dict()
for user in merged_users:
    users_seen[user] = set()
for user in merged_users:
    if merged_users[user]['frame_length']==[]:continue
    for neighbor in merged_users:
        if neighbor==user:continue
        if merged_users[neighbor]['frame_length']==[]:continue
        if neighbor in users_seen[user]:continue
        if user in users_seen[neighbor]:continue
        n_matching = len(set(merged_users[user]['frame_length']).intersection(set(merged_users[neighbor]['frame_length'])))
        if n_matching!=0:
            if user not in frame_length_edges:
                frame_length_edges[user] = dict()
            frame_length_edges[user][neighbor] = frame_length_weight*n_matching    
            users_seen[user].add(neighbor)
            users_seen[neighbor].add(user)


frame_delta_edges = dict()
users_seen = dict()
for user in merged_users:
    users_seen[user] = set()
for user in merged_users:
    if merged_users[user]['frame_time_delta']==[]:continue
    for neighbor in merged_users:
        if neighbor==user:continue
        if merged_users[neighbor]['frame_time_delta']==[]:continue
        if neighbor in users_seen[user]:continue
        if user in users_seen[neighbor]:continue
        if abs(mean(merged_users[user]['frame_time_delta'])-mean(merged_users[neighbor]['frame_time_delta']))<=frame_delta_thresh:
            if user not in frame_delta_edges:
                frame_delta_edges[user] = dict()
            frame_delta_edges[user][neighbor] = frame_delta_weight    
            users_seen[user].add(neighbor)
            users_seen[neighbor].add(user)

signal_edges = dict()
users_seen = dict()
for user in merged_users:
    users_seen[user] = set()
for user in merged_users:
    if merged_users[user]['signal_strength']==[]:continue
    for neighbor in merged_users:
        if neighbor==user:continue
        if merged_users[neighbor]['signal_strength']==[]:continue
        if neighbor in users_seen[user]:continue
        if user in users_seen[neighbor]:continue
        if abs(mean(merged_users[user]['signal_strength'])-mean(merged_users[neighbor]['signal_strength']))<=signal_thresh:
            if user not in signal_edges:
                signal_edges[user] = dict()
            signal_edges[user][neighbor] = signal_weight    
            users_seen[user].add(neighbor)
            users_seen[neighbor].add(user)


destination_edges = create_matcher('destination_mac_resolved',destination_weight,0,['','Broadcast'])
ssid_edges = create_matcher('ssid',ssid_weight,0,['','Broadcast'])
sr_edges = create_matcher('supported_rates',sr_weight,0,[''])
ch_edges = create_matcher('current_channel',ch_weight,0,[''])
esr_edges = create_matcher('extended_supported_rates',esr_weight,0,[''])
rmcap_edges = create_matcher('rmcap',rmcap_weight,0,[''])
ht_edges = create_matcher('ht_capabilities',ht_weight,0,[''])
htamp_edges = create_matcher('ht_ampduparam',htamp_weight,0,[''])
htmcs_edges = create_matcher('ht_mcsset',htmcs_weight,0,[''])
iant_edges = create_matcher('interworking_access_network_type',iant_weight,0,[''])
ii_edges = create_matcher('interworking_internet',ii_weight,0,[''])
ia_edges = create_matcher('interworking_asra',ia_weight,0,[''])
iu_edges = create_matcher('interworking_uesa',iu_weight,0,[''])
ih_edges = create_matcher('interworking_hessid',ih_weight,0,[''])
vhtc_edges = create_matcher('vht_capabilities',vhtc_weight,0,[''])
vhtrxmcs_edges = create_matcher('vht_mcsset_rxmcsmap',vhtrxmcs_weight,0,[''])
vhtrxh_edges = create_matcher('vht_mcsset_rxhighestlonggirate',vhtrxh_weight,0,[''])
vhtrxnst_edges = create_matcher('vht_mcsset_max_nsts_total',vhtrxnst_weight,0,[''])
vhttxmcs_edges = create_matcher('vht_mcsset_txmcsmap',vhttxmcs_weight,0,[''])
vhttxh_edges = create_matcher('vht_mcsset_txhighestlonggirate',vhttxh_weight,0,[''])
vhtext_edges = create_matcher('vht_mcsset_ext_nss_bw_cap',vhtext_weight,0,[''])
vhtres_edges = create_matcher('vht_mcsset_reserved',vhtres_weight,0,[''])
s1c_edges = create_matcher('s1g_control',s1c_weight,0,[''])
s1d_edges = create_matcher('s1g_slot_definition',s1d_weight,0,[''])
s1s_edges = create_matcher('s1g_slot_definition.start_time',s1s_weight,0,[''])
s1i_edges = create_matcher('s1g_channel_indication',s1i_weight,0,[''])
oui_edges = create_matcher('oui',oui_weight,0,[''])
ouit_edges = create_matcher('oui_type',ouit_weight,0,[''])
ie_edges = create_matcher('ie_type',ie_weight,0,[''])
device_edges = []
for device_filter in device_filters:
    device_edges.append(create_matcher(device_filter,device_weight,0,['']))
he_edges = create_matcher('he_mac_caps',he_weight,0,[''])
ext_edges = []
for ext_filter in ext_filters:
    ext_edges.append(create_matcher(ext_filter,ext_info_weight,0,['']))

filters_edges = [[frame_length_edges,frame_delta_edges],
                [signal_edges],
                [destination_edges],
                [ssid_edges,sr_edges,ch_edges,
                 esr_edges,rmcap_edges],
                [ht_edges,htamp_edges,htmcs_edges],
                [iant_edges,ii_edges,ia_edges,
                 iu_edges,ih_edges],
                [vhtc_edges,vhtrxmcs_edges,vhtrxh_edges,
                 vhtrxnst_edges,vhttxmcs_edges,
                 vhttxh_edges,vhtext_edges,vhtres_edges],
                [s1c_edges,s1d_edges,s1s_edges,s1i_edges],
                [oui_edges,ouit_edges,ie_edges]+device_edges,
                [he_edges]+ext_edges
               ]

chosen_edges = [frame_length_edges,ssid_edges,vhtc_edges,sr_edges,esr_edges,oui_edges,ouit_edges,ie_edges]+device_edges
final_edges = dict()
for user in merged_users:
    final_edges[user] = dict()
    for neighbor in merged_users:
        final_edges[user][neighbor] = None
max_weight = -1
min_weight = 100

for chosen_filter in chosen_edges:
    for node in chosen_filter:
        for neighbor in chosen_filter[node]:
            if final_edges[node][neighbor] is None:
                final_edges[node][neighbor] = chosen_filter[node][neighbor]
            else:
                final_edges[node][neighbor] += chosen_filter[node][neighbor]
            if max_weight<final_edges[node][neighbor]:
                max_weight = final_edges[node][neighbor]
            if min_weight>final_edges[node][neighbor]:
                min_weight = final_edges[node][neighbor]

weight_thresh = min_weight + (max_weight-min_weight)*min_weight_ratio
added_nodes = set()
for node in final_edges:
    for neighbor in final_edges[node]:
        if final_edges[node][neighbor] is None: continue
        if final_edges[node][neighbor] < weight_thresh:continue
        vis_weight = min_vis_weight + (max_vis_weight-min_vis_weight)*(final_edges[node][neighbor]-min_weight)/(max_weight-min_weight)
        if neighbor not in added_nodes:
            if vis_weight>0.9*max_vis_weight:
                net.add_node(neighbor,color='#03DAC6',label=neighbor,title=neighbor)
            elif vis_weight>0.5*max_vis_weight:
                net.add_node(neighbor,color="#da03b3",label=neighbor,title=neighbor)
            else:
                net.add_node(neighbor,label=neighbor,title=neighbor)
        
        if node not in added_nodes:
            net.add_node(node,color="#F07900",label=node,title=node)
            
        if vis_weight>0.9*max_vis_weight:
            net.add_edge(node,neighbor,value=vis_weight,color="#FF00FF")
        else:
            net.add_edge(node,neighbor,value=vis_weight,color="#FFFFFF")

net.save_graph(graph_name)
