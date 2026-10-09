"""Revision 07 environment dressing. Original geometry, dimensions in metres.

Large props have colliders; small fittings are material-batched. Central routes
remain clear. This is a fictional prison adaptation, not a measured restoration.
"""
import math
import numpy as np
from geometry import cylinder, ellipsoid, tube, lathe
import unity_writer as uw


def add_details(a, parent, lights):
    root = uw.Node('Alcatraz lived-in spaces / Revision 07', parent)
    box, batch, solid, sign = a.b_box, a.batched, a.slab, a.sign
    uw.material('Alc_Paper', [.72, .70, .60, 1], .98)
    uw.material('Alc_CourtPaint', [.78, .77, .62, 1], .97)
    uw.material('Alc_Laundry', [.62, .65, .58, 1], .96,
                texture='Assets/_DesertShift/Art/Textures/Cloth_Base.png', tiling=3)

    # Broadway fittings sit above head height and outside cell/gallery exits.
    for x in [-25.9, 25.9]:
        batch('Cellhouse services', 'Alc_Iron', tube([(x, 38.7, -40), (x, 38.7, 41)], .07, 8))
        for z in [-39, -19, 1, 21, 40]:
            batch('Cellhouse services', 'Alc_Iron', tube([(x, 32.5, z), (x, 38.7, z)], .038, 6))
            box('Cellhouse junction boxes', 'Alc_DarkSteel', (x, 32.45, z), (.17, .48, .36))
    for x in [-12, 12]:
        for z in [-28, -4, 20]:
            box('Overhead gallery beams', 'Alc_Iron', (x, 38.9, z), (.15, .19, 10))
    sign(root, 'Mess hall direction', (0, 32.65, 42.98), 'DINING HALL  /  COUNTS AT 18:00', (4.4, .6), 180)
    sign(root, 'A block direction', (12.8, 32.2, 30), 'A BLOCK  /  EAST GALLERY', (3.5, .54), 180)
    sign(root, 'Cellhouse noticeboard', (-25.98, 32.1, -37.5),
         'PRISON ROUTINE\n06:30 COUNT   /   07:00 BREAKFAST\n08:00 WORK DETAIL   /   12:00 MEAL\n13:00 YARD   /   18:00 EVENING COUNT', (3.8, 1.4), 90)
    # A readable ID beside the actual player's door, with no collider over the exit.
    sign(root, 'Elias cell identity', (-2.72, 32.18, a.CELL_Z + .7), 'B-04\nE. VALE', (.55, .32), 90)

    # Dining tables: trays, bowls and cups add scale without occupying aisles.
    for x in [-15, -7, 1, 9, 17]:
        for z in [51, 58]:
            for dx in [-1.25, 0, 1.25]:
                for dz in [-.28, .28]:
                    box('Dining trays', 'Alc_Iron', (x+dx, 30.845, z+dz), (.45, .018, .28))
                    batch('Dining bowls', 'Alc_White', lathe([(-.02,.1), (0,.13), (.045,.15), (.06,.145)], 12), (x+dx-.09,30.87,z+dz))
                    batch('Dining cups', 'Alc_White', cylinder(.042,.09,10), (x+dx+.15,30.9,z+dz))
    for x in [-19.5, 19.5]:
        solid('Dining waste station', root, (x,30.53,47.2), (.75,1.06,.65), 'Alc_Painted')
        box('Waste station lids', 'Alc_DarkSteel', (x,31.08,47.2), (.79,.05,.69))
    # Food service grilles above the counter, with serving openings below.
    for x in np.arange(-15,15.1,.38):
        box('Kitchen service grilles','Alc_DarkSteel',(float(x),32.65,64.25),(.032,2.25,.04))
    for y in [31.54,33.76]:box('Kitchen service rails','Alc_Iron',(0,y,64.25),(30,.065,.055))
    sign(root,'Dining routine',(0,34.25,65.34),'ALCATRAZ MESS HALL\nRETURN ALL TRAYS AND UTENSILS',(6,1),180)
    for x in [-15,0,15]:
        solid('Kitchen preparation cabinet',root,(x,30.50,65.2),(3,1,1),'Alc_Painted')
        a.light(lights,'Dining task light',(x,35.9,55.5),2.6,11,(.92,.94,.89))

    # Shower room: changing benches, water valves, hooks and floor drains.
    for x in [5,8,11,14,17]:
        batch('Shower valves','Alc_Iron',cylinder(.10,.04,12),(x,31.23,-46.46),rot=(90,0,0))
        box('Shower taps','Alc_DarkSteel',(x,31.23,-46.5),(.18,.022,.035))
        for dz in [-.06,0,.06]:box('Shower drain grilles','Alc_Iron',(x,30.048,-48+dz),(.21,.006,.012))
    for x in [5.5,18.4]:
        solid('Changing bench',root,(x,30.46,-52.6),(3,.10,.45),'Alc_Wood')
        for dx in [-1.1,1.1]:box('Changing bench legs','Alc_DarkSteel',(x+dx,30.22,-52.6),(.06,.44,.32))
        box('Folded towel','Alc_Laundry',(x,30.57,-52.6),(.44,.1,.32))
    sign(root,'Shower room rules',(21.87,32.45,-50.5),'SHOWER DETAIL\nKEEP THE AISLE CLEAR',(2.6,.8),-90)

    # New Industries: six workstations and laundry, retaining a wide centre aisle.
    for x in [-47,-29]:
        for z in [111,122,133]:
            solid('Industries workbench',root,(x,10.13,z),(4.8,.13,1.6),'Alc_Wood')
            for dx in [-1.9,1.9]:box('Workbench legs','Alc_Iron',(x+dx,9.7,z),(.09,.8,1.35))
            solid('Industrial machine pedestal',root,(x,10.52,z),(1.30,.64,.58),'Alc_Painted',False)
            box('Industrial machine arm','Alc_Iron',(x+.45,10.92,z),(.85,.13,.22))
            batch('Machine wheels','Alc_DarkSteel',cylinder(.24,.07,16),(x-.67,10.71,z),rot=(0,0,90))
            box('Folded work cloth','Alc_Laundry',(x+1.5,10.30,z),(.72,.17,.8))
            solid('Work stool',root,(x,9.78,z-1.45),(.48,.11,.48),'Alc_Wood')
            for dx in [-.17,.17]:box('Work stool legs','Alc_Iron',(x+dx,9.52,z-1.45),(.04,.46,.32))
    for x in [-50,-45,-31,-26]:
        solid('Laundry sorting bin',root,(x,9.87,139.5),(2.2,1.14,1.9),'Alc_Iron')
        for dz in [-.55,0,.55]:box('Linen bundles','Alc_Laundry',(x,10.53,139.5+dz),(1.8,.24,.42))
    sign(root,'Industries safety',( -38,12.2,142.34),'WORK DETAIL\nTOOLS COUNTED BEFORE RELEASE',(5.5,1),180)
    for z in [111,122,133]:a.light(lights,'Industries task lamp',(-38,15.5,z),2.8,13,(.90,.94,.91))

    # Storehouse shelves stay at either side of a broad loading aisle.
    for x in [59,81]:
        for z in [-41,-30,-19]:
            solid('Storehouse shelf footprint',root,(x,6.35,z),(2.1,2.7,4.3),'Alc_Iron')
            # Displayed shelf front is broken into levels, not an opaque block.
            n=uw.Node.all[-1]
            n.parts=[part for part in n.parts if part[0] not in (23,33)]
            n.mesh=n.mat=None
            for dx in [-1,1]:
                for dz in [-2,2]:box('Shelf uprights','Alc_Iron',(x+dx,6.35,z+dz),(.065,2.7,.065))
            for y in [5.15,6.25,7.4]:
                box('Shelf platforms','Alc_Wood',(x,y,z),(2.1,.08,4.3))
                for dz in [-1.35,0,1.35]:
                    box('Supply crates','Alc_Wood',(x,y+.42,z+dz),(1.7,.76,1.04))
                    for dx in [-.65,.65]:box('Crate bands','Alc_DarkSteel',(x+dx,y+.42,z+dz),(.035,.78,1.055))
    sign(root,'Storehouse loading',(70,8,-10.66),'STOREHOUSE\nINVENTORY / RECEIVING',(5.5,.95),180)

    # Small half-court in the quiet southern corner of the recreation yard.
    for x in [-68,-60]:box('Yard court paint','Alc_CourtPaint',(x,27.294,25.4),(.07,.006,6.4))
    for z in [22.2,28.6]:box('Yard court paint','Alc_CourtPaint',(-64,27.294,z),(8,.006,.07))
    solid('Basketball support',root,(-64,29.0,21.65),(.13,3.44,.13),'Alc_DarkSteel')
    solid('Basketball backboard',root,(-64,30.75,22.08),(1.65,.95,.07),'Alc_White',False)
    points=[(-64+.23*math.cos(t),30.37,22.39+.23*math.sin(t)) for t in np.linspace(0,math.tau,25)]
    batch('Basketball ring','Alc_Rust',tube(points,.022,6))
    for t in np.linspace(0,math.tau,10,endpoint=False):
        batch('Basketball net','Alc_White',tube([(-64+.23*math.cos(t),30.35,22.39+.23*math.sin(t)),(-64+.14*math.cos(t+.4),30.02,22.39+.14*math.sin(t+.4))],.005,4))

    # Landing details flank the dock approach so the access route stays open.
    for x in [91,98]:
        solid('Dock waiting bench',root,(x,5.48,-52.4),(3,.12,.55),'Alc_Wood')
        for dx in [-1,1]:box('Dock bench legs','Alc_DarkSteel',(x+dx,5.22,-52.4),(.08,.44,.42))
    for x in [112,121]:
        batch('Wharf rope coil','Alc_Wood',lathe([(-.025,.25),(.025,.25),(.025,.43),(-.025,.43),(-.025,.25)],24),(x,4.985,-57.5))
    sign(root,'Dock wayfinding',(90.7,7.3,-72.45),'CELLHOUSE  /  UP THE HILL\nWORK DETAIL  /  NORTH ROAD',(5.6,.85),180)

    a.flush_batches(root)
    return root
