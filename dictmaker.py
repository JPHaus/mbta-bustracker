# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 03:34:59 2016

@author: Rob
"""
import csv
import json, os

alldicts = ['shapepathdict', 'routenamesdict', 'routeinfodict', 'tripshapedict', 
            'shaperoutedict', 'routeshapedict', 'shapestopsdict',
                'routestopsdict', 'stoproutesdict', 'stopinfodict',
                'shapeinfodict', 'shapefinderdict', 'shapestopseqdict'] 
#Summary of dictionaries:
#shapepathdict - shape_id : [list of latlon path points]
#routenamesdict - route_id : route_name
#tripshapedict - trip_id : shape_id
#shaperoutedict - shape_id : route_id
#routeshapedict - route_id : [list of shape_ids]
#shapestopsdict - shape_id : [List of stops in order] 
#routestopsdict - route_id : [List of stops for that route]
#stoproutesdict - stop_id : [List of routes for that stop]
#shapeinfodict - shape_id : {Dict of 'route_id', 'destination', 'direction'}  
#shapefinderdict - (route_id, direction) : {Dict of destination : shape_id}
#stopinfodict - stop_id : {Dict of 'stop_id', 'stop_name', 'lat', 'lon', 'parent' (if a child), 'children' (if a parent)}}
#shapestopseqdict - shape_id : {Dict of stop_seq : stop_point_index} 

def distll(lat1, lon1, lat2, lon2):
    return ((111120*(lat1 - lat2))**2 + (82600*(lon1 - lon2))**2)**.5   

def angularSquaredDist(lat1, lon1, lat2, lon2):
    '''
    calculates a number proportional to the squared distance, computationally 
    much more efficient than calculating the distance
    '''
    dlon = lon1 - lon2
    dlat = lat1 - lat2
    return dlat**2 + (.742*dlon)**2

def findClosestPoint(lat, lon, path):
    '''
    takes a (vehicle) lat and lon and a path (list of (lat, lon)) and returns 
    the INDEX of the path point closest to the given location
    '''
    closest_i = 0
    min_asdist = 99999
    numpoints = len(path)
    for i in range(numpoints):
        pathlat, pathlon = path[i]
        asdist = angularSquaredDist(lat, lon, pathlat, pathlon)
        if asdist < min_asdist:
            closest_i = i
            min_asdist = asdist
    return closest_i
    
    
def makeRouteNamesDict(filename = 'MBTA_GTFS_texts/routes.txt'):
    #reads the 'routes.txt' file and returns a dictionary of 
    # route_id : route_name
    # WARNING: MUST MANUALLY ADJUST ENTRY FOR SL WATERLINE in txt file
    routenamesdict = dict()
    with open(filename) as f:
        for d in csv.DictReader(f):
            route_id = d["route_id"]
            if d["route_short_name"] == '':
                routename = d["route_long_name"]
            else:
                routename = d["route_short_name"]
            if routename in 'BCDE':
                routename = route_id
            routenamesdict[route_id] = routename       
    return routenamesdict
    
    
def makeRouteInfoDict(filename = 'MBTA_GTFS_texts/routes.txt'):
    #reads the 'routes.txt' file and returns a dictionary of 
    # route_id : {}
    # WARNING: MUST MANUALLY ADJUST ENTRY FOR SL WATERLINE in txt file
    routeinfodict = dict()
    type_dict = {"0":"trolley", "1":"subway", "2":"CR", "3":"bus", "4":"ferry"}
    with open(filename) as f:
        for d in csv.DictReader(f):
            route_dict = dict()
            route_id = d["route_id"]
            route_dict["id"] = route_id
            if d["route_short_name"] == '':
                routename = d["route_long_name"]
            else:
                routename = d["route_short_name"]
            if routename in 'BCDE':
                routename = route_id
            route_dict["name"] = routename
            route_dict["activity"] = 0
            route_dict["sort_order"] = int(d["route_sort_order"])
            route_dict["key"] = d["route_desc"][:3] == "Key"
            route_dict["type"] = type_dict.get(d["route_type"], "other")            
            routeinfodict[route_id] = route_dict     
    return routeinfodict
    
    
def file_to_dict(filename, keyfn, valfn):
    with open(filename) as f:
        return {keyfn(d): valfn(d) for d in csv.DictReader(f)}
        

def makeTripShapeDict(filename = 'MBTA_GTFS_texts/trips.txt'):
    #reads the 'trips.txt' file and returns a dictionary of 
    # trip_id : shape_id 
    return file_to_dict(filename, lambda d: d["trip_id"], lambda d: d["shape_id"])

    
def makeShapeRouteDict(routenamesdict, filename = 'MBTA_GTFS_texts/trips.txt'):
    #reads the 'trips.txt' file and returns a dictionary of 
    # shape_id : route_id 
    return file_to_dict(filename, lambda d: d["shape_id"], lambda d: d["route_id"])

    
def makeRouteShapeDict(shaperoutedict):
    #inverts the shaperoutedict and returns a dictionary of 
    # route_id : [List of shape_ids]
    routeshapedict = dict()
    for shape_id in shaperoutedict:
        route_id = shaperoutedict[shape_id] 
        if route_id in routeshapedict:
            routeshapedict[route_id].append(shape_id)
        else:
            routeshapedict[route_id] = [shape_id]
    return routeshapedict    
    
    
def makeShapePathDict(shaperoutedict, filename = 'MBTA_GTFS_texts/shapes.txt'):
    #reads the 'shapes.txt' file and returns a dictionary of 
    # shape_id : [list of latlon path points]
    shapepathdict = dict([(shape_id, []) for shape_id in shaperoutedict])
    with open(filename) as f:
        for d in csv.DictReader(f):
            shape_id = d["shape_id"]
            if shape_id in shapepathdict:
                latlon = (float(d["shape_pt_lat"]), float(d["shape_pt_lon"]))
                shapepathdict[shape_id].append((int(d["shape_pt_sequence"]),latlon))
        for shape_id in shaperoutedict.keys():
            shapepathdict[shape_id].sort()
            shapepathdict[shape_id] = [x[1] for x in shapepathdict[shape_id]]
    return shapepathdict


def makeStopsDicts(tripshapedict, shaperoutedict,
                   filename = 'MBTA_GTFS_texts/stop_times.txt'):
    #reads the 'stop_times.txt' file and returns two dictionaries of 
    # shapestopsdict shape_id : [List of stops in order] 
    # routestopsdict route_id : [List of stops for that route]
    tripstopsdict = dict()
    tripstopseqstopiddict = dict()
    with open(filename) as f:
        for d in csv.DictReader(f):
            trip_id = d["trip_id"]
            stop_id = d["stop_id"]
            stop_seq = int(d["stop_sequence"])
            if trip_id in tripstopsdict:
                tripstopsdict[trip_id].append((stop_seq, stop_id))
            else:
                tripstopsdict[trip_id] = [(stop_seq, stop_id)]

    for trip_id in tripstopsdict:
        tmp = tripstopsdict[trip_id]
        tmp.sort(key = lambda x : x[0])
        tripstopsdict[trip_id] = [x[1] for x in tmp]
        tripstopseqstopiddict[trip_id] = tmp
        
    shapestopsdict = dict()  
    shapestopseqstopiddict = dict()
    for trip_id in tripstopsdict:
        shape_id = tripshapedict[trip_id]
        if shape_id not in shapestopsdict:
            shapestopsdict[shape_id] = tripstopsdict[trip_id] 
            shapestopseqstopiddict[shape_id] = tripstopseqstopiddict[trip_id]
        elif len(tripstopsdict[trip_id]) > len(shapestopsdict[shape_id]):
            shapestopsdict[shape_id] = tripstopsdict[trip_id]
            shapestopseqstopiddict[shape_id] = tripstopseqstopiddict[trip_id]
    routestopsdict = dict()
    for shape_id in shapestopsdict:
        route_id = shaperoutedict[shape_id]
        if route_id in routestopsdict:
            routestopsdict[route_id] = routestopsdict[route_id].union(shapestopsdict[shape_id])
        else:
            routestopsdict[route_id] = set(shapestopsdict[shape_id])
    for route_id in routestopsdict:
        routestopsdict[route_id] = list(routestopsdict[route_id])
    return shapestopsdict, routestopsdict, shapestopseqstopiddict
    
def makeStopRoutesDict(routestopsdict):
    #inverts the routestopsdict to create a dict of stop_id : [List of routes for that stop]
    stoproutesdict = dict()
    for route_id in routestopsdict:
        for stop_id in routestopsdict[route_id]:
            if stop_id in stoproutesdict:
                stoproutesdict[stop_id].add(route_id)
            else:
                stoproutesdict[stop_id] = set([route_id])
    for stop_id in stoproutesdict:
        stoproutesdict[stop_id] = sorted(list(stoproutesdict[stop_id]))
    return stoproutesdict


def makeShapeInfoDict(shaperoutedict, filename = 'MBTA_GTFS_texts/trips.txt'):
    #reads the 'trips.txt' file and returns a dictionary of 
    # shape_id : {Dict of 'route_id', 'destination', 'direction'}
    shapeinfodict = dict()
    with open(filename) as f:
        for d in csv.DictReader(f):
            shape_id = d["shape_id"]
            if shape_id in shaperoutedict:
                route_id = d["route_id"]
                destination = d["trip_headsign"]
                direction = d["direction_id"]
                shapeinfodict[shape_id] = {'route_id' : route_id, 
                                            'destination' : destination,
                                            'direction' : direction}
    return shapeinfodict
    
    
def makeShapeFinderDict(shapeinfodict, shapepathdict):
    # inverts the shapeinfodict for use in obtaining a shape_id for unscheduled ("Added") trips
    # 'route_id_direction' : {destination : shape_id}
    # if there are multiple shapes that have the same route_id, direction and destination, it returns the longest one
    shapefinderdict = dict()
    for shape_id in shapeinfodict:
        info = shapeinfodict[shape_id]
        route_id, destination, direction = info['route_id'], info['destination'], info['direction']
        key = route_id + '_' + direction
        if key in shapefinderdict:
            entry = shapefinderdict[key]
            if len(shapepathdict[shape_id]) > len(shapepathdict[entry['default']]):
                entry['default'] = shape_id
            if destination not in entry or len(shapepathdict[shape_id]) > len(shapepathdict[entry[destination]]):
                entry[destination] = shape_id
        else:
            shapefinderdict[key] = {destination: shape_id, 'default': shape_id}
    return shapefinderdict


def makeStopInfoDict(stoproutesdict, shapeinfodict, shapestopsdict, 
                     filename = 'MBTA_GTFS_texts/stops.txt'):
    #reads the 'stops.txt' file and returns a dictionary of 
    #stop_id : {Dict of 'stop_id', 'stop_name', 'lat', 'lon', 'parent' (if a child), 'children' (if a parent)}}
    stopinfodict = dict()
    with open(filename) as f:
        for d in csv.DictReader(f):
            stop_id = d["stop_id"]
            if stop_id in stoproutesdict or stop_id[0] == 'p':
                stop_name = d["stop_name"]
                parent = d["parent_station"]
                lat = float(d["stop_lat"])
                lon = float(d["stop_lon"])
                stopinfodict[stop_id] = dict([('stop_id', stop_id),
                                             ('stop_name', stop_name), 
                                             ('lat', lat),
                                             ('lon', lon),
                                             ('route_ids', stoproutesdict.get(stop_id))])
                if stop_id[0] == 'p':
                    stopinfodict[stop_id]['children'] = []
                if parent:
                    #i.e. if you HAVE a parent
                    stopinfodict[stop_id]['parent'] = parent
    
    for stop_id in stopinfodict:
        parent = stopinfodict[stop_id].get('parent')
        if parent:
            stopinfodict[parent]['children'].append(stop_id)
    
    for stop_id in stopinfodict:
        stopinfodict[stop_id]['one_way'] = set()
        if stopinfodict[stop_id].get('children'):
            route_ids = []
            for child_id in stopinfodict[stop_id]['children']:
                route_ids += stoproutesdict.get(child_id, []) 
            route_ids = sorted(list(set(route_ids)))
            stopinfodict[stop_id]['route_ids'] = route_ids
    for shape_id in shapeinfodict:
        direction = shapeinfodict[shape_id]['direction']
        stoplist = shapestopsdict.get(shape_id, [])
        for stop_id in stoplist:
            stopinfodict[stop_id]['one_way'].add(direction)
    for stop_id in stopinfodict:
        one_way = list(stopinfodict[stop_id]['one_way'])
        if (len(one_way) == 2) or (len(one_way) == 0): 
            del stopinfodict[stop_id]['one_way']
        else:
            stopinfodict[stop_id]['one_way'] = one_way[0]
    return stopinfodict
    

def makeShapeStopSeqDict(shapepathdict, shapestopseqstopiddict, stopinfodict):
    '''
    returns a dictionary of
    shape_id :  {Dict of stop_sequence : stop_point_index}
    stop_sequence is a sort of index for each stop in a shape.  For bus shapes,
    the stop sequence always goes ['1', '2', ...].  But for trains, the stop 
    sequence is (annoyingly) ['1', '10', '20', '30', '80', '90', ...] or something  
    silly like that.    
    '''
    shapestopseqdict = dict()
    for shape_id in shapepathdict:
        path = shapepathdict[shape_id]
        stopseq_stopid_list = shapestopseqstopiddict.get(shape_id, [])
        stopseqdict = dict()
        for stopseq_stopid in stopseq_stopid_list:
            stopseq, stop_id = stopseq_stopid
            stopinfo = stopinfodict[stop_id]
            stopseqdict[stopseq] = findClosestPoint(stopinfo['lat'], stopinfo['lon'], path)
        shapestopseqdict[shape_id] = stopseqdict
    return shapestopseqdict




def makeAllDicts(folder = 'data'):
    if not os.path.exists(folder):
        os.mkdir(folder)
    routenamesdict = makeRouteNamesDict()
    routeinfodict = makeRouteInfoDict()
    tripshapedict = makeTripShapeDict()
    shaperoutedict = makeShapeRouteDict(routenamesdict)
    routeshapedict = makeRouteShapeDict(shaperoutedict)
    shapepathdict = makeShapePathDict(shaperoutedict)
    shapestopsdict, routestopsdict, shapestopseqstopiddict = makeStopsDicts(tripshapedict, shaperoutedict)
    stoproutesdict = makeStopRoutesDict(routestopsdict)
    shapeinfodict = makeShapeInfoDict(shaperoutedict)
    shapefinderdict = makeShapeFinderDict(shapeinfodict, shapepathdict)
    stopinfodict = makeStopInfoDict(stoproutesdict, shapeinfodict, shapestopsdict)
    shapestopseqdict = makeShapeStopSeqDict(shapepathdict, shapestopseqstopiddict, stopinfodict)
    for dic in alldicts:
        f = open(folder + '/' + dic + '.json', 'w')
        json.dump(eval(dic), f)
        f.close()
 



def makeShapePathSequenceDict(shaperoutedict, filename = 'MBTA_GTFS_texts/shapes.txt'):
    #reads the 'shapes.txt' file and returns a dictionary of 
    # shape_id : [list of LISTS of [latlon path points]] divided by the shape_pt_seq field
    f = open(filename, 'r')
    f.readline()
    rawlines = f.readlines()
    f.close()
    splitlines = [l.split(',') for l in rawlines]
    shape_ids = set()
    for l in splitlines:
        shape_id = l[0].strip('"')
        if shaperoutedict.get(shape_id, 'CR')[0] != 'C':
            shape_ids.add(shape_id)
    shapepathseqdict = dict([(shape_id, []) for shape_id in shape_ids])
    for l in splitlines:
        if l[0].strip('"') in shape_ids:
            latlon = (float(l[1].strip('"')), float(l[2].strip('"')))
            shape_pt_seq = int(l[3])
            shapepathseqdict[l[0].strip('"')].append((shape_pt_seq,latlon))
    for shape_id in shape_ids:
        tmp = sorted(shapepathseqdict[shape_id])
        tmp = [(int(str(x[0])[:-4]), x[1]) for x in tmp]
        shapepathseqdict[shape_id] = tmp
    return shapepathseqdict


def makeShapeTripsDict(tripshapedict):
    # inverts the tripshapedict to create a dict of shape_id : [List of trip_ids for that shape_id]
    shapetripsdict = dict()
    for trip_id in tripshapedict:
        shape_id = tripshapedict[trip_id]
        if shape_id in shapetripsdict:
            shapetripsdict[shape_id].add(trip_id)
        else:
            shapetripsdict[shape_id] = set([trip_id])
    for shape_id in shapetripsdict:
        shapetripsdict[shape_id] = sorted(list(shapetripsdict[shape_id]))
    return shapetripsdict

