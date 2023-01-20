import json
import random
def dict_raise_on_duplicates(ordered_pairs):
    """Convert duplicate keys to JSON array."""
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

def generate_mac():
    return ':'.join(''.join(random.choice(letters) for i in range(2)) for j in range(6))

with open('Collected_Data/new_static.json','r') as f:
    data = f.read()

letters = [char for char in '0123456789abcdef']
parsed_data = json.loads(data, object_pairs_hook=dict_raise_on_duplicates) 

filtered_packets = [elem for elem in parsed_data if 'wlan' in elem['_source']['layers']]
filtered_packets = [elem for elem in filtered_packets if 'wlan.mgt' in elem['_source']['layers']]
filtered_packets = [elem for elem in filtered_packets if 'wlan.fc.type_subtype' in elem['_source']['layers']['wlan']]
filtered_packets = [elem for elem in filtered_packets if elem['_source']['layers']['wlan']['wlan.fc.type_subtype']=='0x0004']
filtered_packets = [elem for elem in filtered_packets if len(elem['_source']['layers']['wlan.mgt']['wlan.tagged.all'])>0]
filtered_packets = [elem for elem in filtered_packets if 'wlan.ta_resolved' in elem['_source']['layers']['wlan']]

randomized_mapping = dict()
mapping = dict()
for frame in filtered_packets:
    sa = frame['_source']['layers']['wlan']['wlan.sa']
    sa_resolved = frame['_source']['layers']['wlan']['wlan.sa_resolved']
    ta = frame['_source']['layers']['wlan']['wlan.ta']
    ta_resolved = frame['_source']['layers']['wlan']['wlan.ta_resolved']
    mapping[sa] = [sa]
    mapping[sa].append(sa_resolved)
    mapping[sa].append(ta)
    mapping[sa].append(ta_resolved)
    if sa in randomized_mapping:
        continue
    random_sa = generate_mac()
    while random_sa in randomized_mapping:
        random_sa = generate_mac()
    randomized_mapping[sa] = random_sa
for elem in randomized_mapping:
    for subelem in mapping[elem]:
        data = data.replace(subelem,randomized_mapping[elem])
with open('anon.json','w+') as f:
    f.write(data)