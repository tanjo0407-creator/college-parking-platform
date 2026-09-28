import json
import urllib.request


def test_api():
    base = 'http://127.0.0.1:8000'
    
    # 1. Overview
    req = urllib.request.urlopen(f'{base}/api/campus/overview')
    overview = json.loads(req.read().decode())
    print('1. Campus Overview Metrics:', overview['metrics'])
    print('   Zones Count:', len(overview['zones']))

    # 2. Zone Detail
    req = urllib.request.urlopen(f'{base}/api/parking/zone/1')
    zone1 = json.loads(req.read().decode())
    print('2. Zone 1 Code:', zone1['zone_code'], 'Spots Count:', len(zone1['spots']))

    # 3. Suggest for Student 4W (should be denied)
    # Let's find Chloe Bennett's user & vehicle id
    req = urllib.request.urlopen(f'{base}/api/users')
    users = json.loads(req.read().decode())
    student_4w_user = next(u for u in users if u['name'] == 'Chloe Bennett')
    chloe_v = student_4w_user['vehicles'][0]

    post_data = json.dumps({'user_id': student_4w_user['id'], 'vehicle_id': chloe_v['id']}).encode()
    req = urllib.request.Request(f'{base}/api/parking/suggest', data=post_data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode())
    print('3. Suggest Student 4W -> Allowed:', data['allowed'], 'Rule Code:', data['rule_code'])

    # 4. Suggest for Faculty 4W (Dr. Sarah Mitchell)
    faculty_user = next(u for u in users if u['name'] == 'Dr. Sarah Mitchell')
    faculty_v = faculty_user['vehicles'][0]
    post_data = json.dumps({'user_id': faculty_user['id'], 'vehicle_id': faculty_v['id']}).encode()
    req = urllib.request.Request(f'{base}/api/parking/suggest', data=post_data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode())
    print('4. Suggest Faculty 4W -> Allowed:', data['allowed'], 'Spot:', data['best_spot']['spot_code'])

    # 5. Check-In & Check-Out
    best_spot_code = data['best_spot']['spot_code']
    ci_data = json.dumps({'spot_code': best_spot_code, 'user_id': faculty_user['id'], 'vehicle_id': faculty_v['id']}).encode()
    req = urllib.request.Request(f'{base}/api/parking/check-in', data=ci_data, headers={'Content-Type': 'application/json'})
    ci_resp = json.loads(urllib.request.urlopen(req).read().decode())
    print('5. Check-In Result:', ci_resp['success'], 'Message:', ci_resp['message'])

    co_data = json.dumps({'spot_code': best_spot_code}).encode()
    req = urllib.request.Request(f'{base}/api/parking/check-out', data=co_data, headers={'Content-Type': 'application/json'})
    co_resp = json.loads(urllib.request.urlopen(req).read().decode())
    print('6. Check-Out Result:', co_resp['success'], 'Duration:', co_resp['duration_minutes'], 'min')

    # 7. Visitor Register
    vis_data = json.dumps({
        'name': 'Prof. Henry Higgins',
        'phone': '+1-555-4499',
        'license_plate': 'VIS-EXP-999',
        'vehicle_type': 'FOUR_WHEELER',
        'purpose': 'External Examiner'
    }).encode()
    req = urllib.request.Request(f'{base}/api/visitors/register', data=vis_data, headers={'Content-Type': 'application/json'})
    vis_resp = json.loads(urllib.request.urlopen(req).read().decode())
    print('7. Visitor Registration:', vis_resp['success'], 'Assigned Zone:', vis_resp['assigned_zone'], 'Suggested Spot:', vis_resp['suggested_spot'])

    # 9. Register New User (Any Role)
    for role, vtype, name, plate in [
        ('STUDENT', 'FOUR_WHEELER', 'Freshman John', 'REG-ST-4W'),
        ('STUDENT', 'TWO_WHEELER', 'Freshman Alice', 'REG-ST-2W'),
        ('FACULTY', 'FOUR_WHEELER', 'Prof. Alan Turing', 'REG-FA-4W'),
        ('ADMIN', 'TWO_WHEELER', 'Officer Smith', 'REG-AD-2W'),
        ('VISITOR', 'FOUR_WHEELER', 'Auditor Bob', 'REG-VI-4W'),
    ]:
        reg_data = json.dumps({
            'name': name,
            'phone': '+1-555-8888',
            'role': role,
            'department_or_purpose': 'Computer Science',
            'license_plate': plate,
            'vehicle_type': vtype
        }).encode()
        req = urllib.request.Request(f'{base}/api/users/register', data=reg_data, headers={'Content-Type': 'application/json'})
        reg_resp = json.loads(urllib.request.urlopen(req).read().decode())
        allowed = reg_resp['rule_evaluation']['allowed']
        rule = reg_resp['rule_evaluation']['rule_code']
        spot = reg_resp['suggested_spot']
        print(f'9. Registered {name} ({role}, {vtype}) -> Allowed: {allowed}, Rule: {rule}, Spot: {spot}')

if __name__ == '__main__':
    test_api()
