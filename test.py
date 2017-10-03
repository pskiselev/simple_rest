import requests

authentication = ('kostuk', 'NeENgy')
ids = [421350,1670,3571,3581,29174,14662,47489,39516,248103,3589,305493,14652,218868,178288,92720,33307,318058,14657,50840,66082,217372,29329,32000,3590,3575,33308,199400,108818,
4654,4649,16735,815,5804,28042,5879,26852,26764,13999,11256,174459,49382,8988,5777,44824,26636,19105,9572,26654,5955,16876,40437,8989,5845]

r = requests.post('http://138.201.53.190:5000/api/v1.0/clear',
                  json={
                   "match_id": 845559,
                   "player_id": 5845
                  },
                  auth=authentication)

response = r.json()
print(response)



# for i in ids:
#  r = requests.post('http://138.201.53.190:5000/api/v1.0/clear',
#                           json={
#                            "match_id": 845559,
#                            "player_id": i
#                           },
#                           auth=authentication)

