import bpy
from math import radians
from bpy.app.handlers import persistent
from . import armature_rename
from .armature_creation import armature

class Prefixes: #Container for other prefixes
    helper = 'hlp_'
    helper2 = 'ValveBiped.hlp_'
    attachment = 'ValveBiped.attachment_'
    attachment2 = 'ValveBiped.Anim_'
    other = 'ValveBiped.'

    ##Helper prefixes##
    #h1 = hlp_
    #h2 = ValveBiped.hlp_

    ##Attachment prefixes##
    #a1 = ValveBiped.attachment
    #a2 = ValveBiped.Anim

    ##Bone prefixes##
    #p1 = Current prefix
    #p2 = ValveBiped.

@persistent
def create_armature(self, context): #Creates new armature class
    vatproperties = bpy.context.scene.vatproperties
    vatinfo = bpy.context.scene.vatinfo

    if vatinfo.creating_armature:
        vatinfo.creating_armature = False

    if vatproperties.target_armature:
        if vatinfo.armature_name != vatproperties.target_armature.name:
            vatinfo.armature_name = ''
            vatinfo.unit = 0

        global arm
        arm = Armature(vatproperties.target_armature)
        vatinfo.armature_name = vatproperties.target_armature.name
    else:
        vatinfo.armature_name = ''
        
@persistent
def armatures_reset(*args):
    vatproperties = bpy.context.scene.vatproperties
    vatinfo = bpy.context.scene.vatinfo

    if vatinfo.armature_name:
        vatproperties.target_armature = bpy.data.objects[vatinfo.armature_name]

class Armature: #Armature base

    def __init__(self, armature):
        vatinfo = bpy.context.scene.vatinfo

        #Basic armature information
        self.armature = armature
        self.armature_real = armature.data

        #Additional armatures
        self.weight_armature = None
        self.weight_armature_real = None
        self.animation_armature = None
        self.animation_armature_real = None

        #Functions executed to gather armature information
        if vatinfo.armature_name:
            self.get_bones(False)
        else:
            self.get_bones(True)
            
        if vatinfo.scheme != -1:
            self.get_unit()
            self.get_armatures()
            self.get_constraints()
            self.set_groups()
            if self.helper_bones:
                self.set_helper_bones()
        else:
            print("Empty armature, cannot proceed")
            
    def get_bones(self, report): #Builds bone lists
        vatproperties = bpy.context.scene.vatproperties
        vatinfo = bpy.context.scene.vatinfo
        armature = self.armature

        if self.armature:
            #Cleans bone list
            self.full_bonelist = []
            self.symmetrical_bones = {'arms': {'clavicle': [], 'upperarm': [], 'forearm': [], 'hand': []}, 'legs': {'thigh': [], 'calf': [], 'foot': [], 'toe0': []}, 'fingers': {'finger0': [], 'finger01': [], 'finger02': [], 'finger1': [], 'finger11': [], 'finger12': [], 'finger2': [], 'finger21': [], 'finger22': [], 'finger3': [], 'finger31': [], 'finger32': [], 'finger4': [], 'finger41': [], 'finger42': []}}
            self.central_bones = {'pelvis': [], 'spine': [], 'spine1': [], 'spine2': [], 'spine3': [], 'spine4': [], 'neck': [], 'head': []}
            self.helper_bones = {'arms': {'trapezius': [], 'shoulder': [], 'bicep': [], 'elbow': [], 'ulna': [], 'wrist': []}, 'legs': {'quadricep': [], 'knee': []}, 'viewmodel': {'thumbroot': [], 'thumbfix': [], 'wrist_helper1': [], 'wrist_helper2': [], 'forearm_driven': [], 'ulna_extra1': [], 'ulna_extra2': [], 'wrist_extra': []}, 'others': {'others': []}}
            self.other_bones = {'forward': [], 'weapon': [], 'attachment': [], 'viewmodel': [], 'root': [], 'others': []}
            self.custom_bones = {'jiggle': [], 'others': []}

            self.full_bonelist = armature.data.bones.keys() #Gets all bones in armature

            #Checks if bone list is empty
            if self.full_bonelist:

                symmetrical_bones_raw = []
                central_bones_raw = []
                helper_bones_raw = []
                other_bones_raw = []
                custom_bones_raw = []

                self.side = []
                helper_bones = []
                central_bones = []

                vatinfo.prefix = ''
                vatinfo.sbox = False
                vatinfo.goldsource = False
                vatinfo.titanfall = False
                vatinfo.sfm
                vatinfo.viewmodel = False
                vatinfo.special_viewmodel = False

                for bone in self.full_bonelist:
                    marked = False
                    #Helper prefix
                    if bone.startswith('hlp_'):
                        helper_bones_raw.append(bone.replace(Prefixes.helper, 'h1'))
                        continue

                    ##Source##
                    elif bone.startswith('ValveBiped.'):
                        if not vatinfo.special_viewmodel:
                            vatinfo.prefix = 'ValveBiped.Bip01_'
                        self.side = ['L_', 'R_', '_L', '_R']
                        helper_bones = ['ulna', 'wrist', 'elbow', 'knee', 'trapezius', 'quad', 'bicep', 'shoulder', 'thumbroot']
                        central_bones = []

                        #Dumb leftover bone with no purpose in some Titanfall armatures
                        if vatinfo.titanfall:
                            self.custom_bones['others'].append('p2.' + bone.replace('ValveBiped.', ''))
                            continue

                        #L4D2 helper prefix, uses 'h2' prefix
                        if bone.startswith('ValveBiped.hlp_'):
                            helper_bones_raw.append(bone.replace('ValveBiped.hlp_', 'h2.'))
                            continue

                        #Attachment bone prefixes
                        elif bone.startswith('ValveBiped.attachment'):
                            other_bones_raw.append(bone.replace('ValveBiped.attachment_', 'a1.'))
                            continue
                        
                        elif bone.startswith('ValveBiped.Anim'):
                            other_bones_raw.append(bone.replace('ValveBiped.Anim_', 'a2.'))
                            continue

                        elif bone == 'ValveBiped.ValveBiped':
                            vatinfo.viewmodel = True
                            self.other_bones['root'].append(bone.replace(Prefixes.other, 'p2.'))
                            continue

                        elif bone == 'ValveBiped.bip_root' or bone == 'ValveBiped.bip_base':
                            vatinfo.prefix = 'ValveBiped.bip_'
                            vatinfo.viewmodel = True
                            vatinfo.special_viewmodel = True
                            self.other_bones['root'].append(bone.replace(vatinfo.prefix, 'p1.'))
                            continue

                    ##Source Filmmaker (Not supported currently)##
                    elif bone.startswith('bip_') and not vatinfo.special_viewmodel:
                        vatinfo.sfm = True
                        vatinfo.prefix = 'bip_'

                    ##Gold Source##
                    elif bone.title().startswith('Bip0') or bone.count('Bone') or bone.count('Dummy'):
                        vatinfo.goldsource = True
                        self.side = [' L ', ' R ', ' L', ' R']
                        helper_bones = []
                        central_bones = []

                        if bone.title().startswith('Bip01'):
                            vatinfo.prefix = 'Bip01'
                        elif bone.title().startswith('Bip02'):
                            vatinfo.prefix = 'Bip02'
                        
                        if bone == vatinfo.prefix:
                            self.other_bones['root'].append(bone)
                            continue
                        
                    ##S&Box##
                    elif vatinfo.sbox or self.full_bonelist.count('root_IK'):
                        vatinfo.sbox = True
                        vatinfo.prefix = ''
                        self.side = ['L_', 'R_', '_L', '_R']
                        helper_bones = ['twist', 'helper']
                        central_bones = ['pelvis', 'spine_0', 'spine_1', 'spine_2', 'neck_0', 'head']

                        if bone.casefold().count('ik'):
                            other_bones_raw.append(bone)
                            continue
                        
                        elif bone.casefold().count('face') or bone.casefold().count('eye'):
                            custom_bones_raw.append(bone)
                            continue
                        
                    ##Titanfall##
                    elif bone.startswith('def') or bone.startswith('ja') or bone.startswith('jx'):
                        vatinfo.titanfall = True
                        vatinfo.prefix = 'def_'
                        self.side = ['L_', 'R_', '_L', '_R']
                        helper_bones = ['forearm', 'elbowb', 'kneeb', 'shouldermid', 'shouldertwist']
                        central_bones = []
                        
                        #Root bone
                        if bone == 'jx_c_delta':
                            self.other_bones['root'].append(bone)
                            continue

                        #Attachments/#Special bones
                        elif bone.startswith('ja') or bone.startswith('jx'):
                            other_bones_raw.append(bone)
                            continue
                    else:
                        self.side = ['L_', 'R_', '_L', '_R']

                    #Central bone set if defined
                    if central_bones:
                        for central in central_bones:
                            if bone.casefold().count(central):
                                if vatinfo.prefix:
                                    central_bones_raw.append(bone.replace(vatinfo.prefix, 'p1.'))
                                else:
                                    central_bones_raw.append(bone)
                                marked = True
                                break
                                
                    #Helper bone set
                    if helper_bones:
                        for helper in helper_bones:
                            if bone.casefold().count(helper):
                                if vatinfo.prefix:
                                    helper_bones_raw.append(bone.replace(vatinfo.prefix, 'p1.'))
                                else:
                                    helper_bones_raw.append(bone)
                                marked = True
                                break

                    if marked:
                        continue

                    if bone.startswith(vatinfo.prefix) or vatinfo.special_viewmodel:
                        bone2 = bone.replace(vatinfo.prefix, '').title()

                        if bone.casefold().count('weapon') or bone.casefold().count('gun') or bone.casefold().count('missile'):
                            if vatinfo.prefix:
                                other_bones_raw.append(bone.replace(vatinfo.prefix, 'p1.'))
                            else:
                                other_bones_raw.append(bone)
                            continue

                        #Default prefix
                        elif bone2.startswith(self.side[0]) or bone2.startswith(self.side[1]): #Symmetrical
                            vatinfo.scheme = 0
                            if vatinfo.prefix:
                                symmetrical_bones_raw.append(bone.replace(vatinfo.prefix, 'p1.'))
                            else:
                                symmetrical_bones_raw.append(bone)
                            continue

                        #Blender Friendly prefix
                        elif bone2.endswith(self.side[2]) or bone2.endswith(self.side[3]):
                            vatinfo.scheme = 1
                            if vatinfo.prefix:
                                symmetrical_bones_raw.append(bone.replace(vatinfo.prefix, 'p1.'))
                            else:
                                symmetrical_bones_raw.append(bone)
                            continue

                        elif vatinfo.prefix:
                            central_bones_raw.append(bone.replace(vatinfo.prefix, 'p1.'))
                            continue

                    if bone.startswith(Prefixes.other):
                        other_bones_raw.append(bone.replace(Prefixes.other, 'p2.'))
                        continue
                                
                    ##No/Different prefix##
                    custom_bones_raw.append(bone)

                #Empty armature
                if not symmetrical_bones_raw and not central_bones_raw and not self.other_bones:
                    vatinfo.scheme = -1

                ###Organizes dictionary from raw lists###

                ##Symmetrical bones##
                if symmetrical_bones_raw:
                    #Bone list order:
                    #arms = clavicle, upperarm, forearm, hand
                    #legs = thigh, calf, foot, toe0
                    #fingers = finger0, finger01, finger02, finger1, finger11...

                    for bone in symmetrical_bones_raw:
                        #L4D special infected viewmodel
                        if vatinfo.special_viewmodel:
                            arms = ['Collar', 'Upperarm', 'Lowerarm', 'Hand']
                            legs = []
                            fingers = ['thumb_0', 'thumb_1', 'thumb_2', 'index_0', 'index_1', 'index_2', 'middle_0', 'middle_1', 'middle_2', 'ring_0', 'ring_1', 'ring_2', 'pinky_0', 'pinky_1', 'pinky_2']

                        #Gold Source
                        elif vatinfo.goldsource:
                            arms = ['Arm', 'Arm1', 'Arm2', 'Hand']
                            legs = ['Leg', 'Leg1', 'Foot', None]
                            fingers = ['Finger0', 'Finger01', 'Finger02', 'Finger1', 'Finger11', 'Finger12', 'Finger2', 'Finger21', 'Finger22', 'Finger3', 'Finger31', 'Finger32', 'Finger4', 'Finger41', 'Finger42']

                            if bone.title().count('Toe'):
                                if bone.title().count('Toe02'):
                                    self.symmetrical_bones['legs'].setdefault('toe02', [])
                                    self.symmetrical_bones['legs']['toe02'].append(bone)
                                    self.symmetrical_bones['legs']['toe02'].sort()
                                    continue
                                elif bone.title().count('Toe01'):
                                    self.symmetrical_bones['legs'].setdefault('toe01', [])
                                    self.symmetrical_bones['legs']['toe01'].append(bone)
                                    self.symmetrical_bones['legs']['toe01'].sort()
                                    continue
                                elif bone.title().count('Toe12'):
                                    self.symmetrical_bones['legs'].setdefault('toe12', [])
                                    self.symmetrical_bones['legs']['toe12'].append(bone)
                                    self.symmetrical_bones['legs']['toe12'].sort()
                                    continue
                                elif bone.title().count('Toe11'):
                                    self.symmetrical_bones['legs'].setdefault('toe11', [])
                                    self.symmetrical_bones['legs']['toe11'].append(bone)
                                    self.symmetrical_bones['legs']['toe11'].sort()
                                    continue
                                elif bone.title().count('Toe1'):
                                    self.symmetrical_bones['legs'].setdefault('toe1', [])
                                    self.symmetrical_bones['legs']['toe1'].append(bone)
                                    self.symmetrical_bones['legs']['toe1'].sort()
                                    continue

                        #Titanfall
                        elif vatinfo.titanfall:
                            arms = ['Clav', 'Shoulder', 'Elbow', 'Wrist']
                            legs = ['Thigh', 'Knee', 'Ankle', 'Ball']
                            fingers = ['finThumbA', 'finThumbB', 'finThumbC', 'finIndexA', 'finIndexB', 'finIndexC', 'finMidA', 'finMidB', 'finMidC', 'finRingA', 'finRingB', 'finRingC', 'finPinkyA', 'finPinkyB', 'finPinkyC']

                            if bone.count('Carpal'):
                                self.symmetrical_bones['fingers'].setdefault('fingercarpal', [])
                                self.symmetrical_bones['fingers']['fingercarpal'].append(bone)
                                self.symmetrical_bones['fingers']['fingercarpal'].sort()
                                continue

                            elif bone.count('thighLow'):
                                self.symmetrical_bones['legs'].setdefault('thighlow', [])
                                self.symmetrical_bones['legs']['thighlow'].append(bone)
                                self.symmetrical_bones['legs']['thighlow'].sort()
                                continue

                            elif bone.count('hip'):
                                self.symmetrical_bones['legs'].setdefault('hip', [])
                                self.symmetrical_bones['legs']['hip'].append(bone)
                                self.symmetrical_bones['legs']['hip'].sort()
                                continue

                        #Sbox
                        elif vatinfo.sbox:
                            arms = ['Clavicle', 'Arm_Upper', 'Arm_Lower', 'Hand']
                            legs = ['Leg_Upper', 'Leg_Lower', 'Ankle', 'Ball']
                            fingers = ['thumb_0', 'thumb_1', 'thumb_2', 'finger_index_0', 'finger_index_1', 'finger_index_2', 'finger_middle_0', 'finger_middle_1', 'finger_middle_2', 'finger_ring_0', 'finger_ring_1', 'finger_ring_2', None, None, None,]
                            
                            if bone.title().count('Hold'):
                                self.other_bones['attachment'].append(bone)
                                self.other_bones['attachment'].sort()
                                continue
                            
                            elif bone.count('finger_index_meta'):
                                self.symmetrical_bones['fingers'].setdefault('indexmeta', [])
                                self.symmetrical_bones['fingers']['indexmeta'].append(bone)
                                self.symmetrical_bones['fingers']['indexmeta'].sort()
                                continue

                            elif bone.count('finger_middle_meta'):
                                self.symmetrical_bones['fingers'].setdefault('middlemeta', [])
                                self.symmetrical_bones['fingers']['middlemeta'].append(bone)
                                self.symmetrical_bones['fingers']['middlemeta'].sort()
                                continue

                            elif bone.count('finger_ring_meta'):
                                self.symmetrical_bones['fingers'].setdefault('ringmeta', [])
                                self.symmetrical_bones['fingers']['ringmeta'].append(bone)
                                self.symmetrical_bones['fingers']['ringmeta'].sort()
                                continue

                        #Source
                        else:
                            arms = ['Clavicle', 'Upperarm', 'Forearm', 'Hand']
                            legs = ['Thigh', 'Calf', 'Foot', 'Toe0']
                            fingers = ['Finger0', 'Finger01', 'Finger02', 'Finger1', 'Finger11', 'Finger12', 'Finger2', 'Finger21', 'Finger22', 'Finger3', 'Finger31', 'Finger32', 'Finger4', 'Finger41', 'Finger42']

                            if bone.title().count('Forearm_Driven'):
                                self.helper_bones['viewmodel']['forearm_driven'].append(bone)
                                self.helper_bones['viewmodel']['forearm_driven'].sort()
                                continue

                        #Inversed due to how some armatures deal with bone names ('Arm, Arm1' for example)
                        if arms:
                            if arms[3]:
                                if bone.title().count(arms[3]):
                                    self.symmetrical_bones['arms']['hand'].append(bone)
                                    self.symmetrical_bones['arms']['hand'].sort()
                                    continue
                            if arms[2]:
                                if bone.title().count(arms[2]):
                                    self.symmetrical_bones['arms']['forearm'].append(bone)
                                    self.symmetrical_bones['arms']['forearm'].sort()
                                    continue
                            if arms[1]:
                                if bone.title().count(arms[1]):
                                    self.symmetrical_bones['arms']['upperarm'].append(bone)
                                    self.symmetrical_bones['arms']['upperarm'].sort()
                                    continue
                            if arms[0]:
                                if bone.title().count(arms[0]):
                                    self.symmetrical_bones['arms']['clavicle'].append(bone)
                                    self.symmetrical_bones['arms']['clavicle'].sort()
                                    continue

                        if legs:
                            if legs[3]:
                                if bone.title().count(legs[3]):
                                    self.symmetrical_bones['legs']['toe0'].append(bone)
                                    self.symmetrical_bones['legs']['toe0'].sort()
                                    continue
                            if legs[2]:
                                if bone.title().count(legs[2]):
                                    self.symmetrical_bones['legs']['foot'].append(bone)
                                    self.symmetrical_bones['legs']['foot'].sort()
                                    continue
                            if legs[1]:
                                if bone.title().count(legs[1]):
                                    self.symmetrical_bones['legs']['calf'].append(bone)
                                    self.symmetrical_bones['legs']['calf'].sort()
                                    continue
                            if legs[0]:
                                if bone.title().count(legs[0]):
                                    self.symmetrical_bones['legs']['thigh'].append(bone)
                                    self.symmetrical_bones['legs']['thigh'].sort()
                                    continue
                        
                        if fingers:
                            if fingers[2]:
                                if bone.count(fingers[2]):
                                    self.symmetrical_bones['fingers']['finger02'].append(bone)
                                    self.symmetrical_bones['fingers']['finger02'].sort()
                                    continue
                            if fingers[1]:
                                if bone.count(fingers[1]):
                                    self.symmetrical_bones['fingers']['finger01'].append(bone)
                                    self.symmetrical_bones['fingers']['finger01'].sort()
                                    continue
                            if fingers[0]:
                                if bone.count(fingers[0]):
                                    self.symmetrical_bones['fingers']['finger0'].append(bone)
                                    self.symmetrical_bones['fingers']['finger0'].sort()
                                    continue

                            if fingers[5]:
                                if bone.count(fingers[5]):
                                    self.symmetrical_bones['fingers']['finger12'].append(bone)
                                    self.symmetrical_bones['fingers']['finger12'].sort()
                                    continue
                            if fingers[4]:
                                if bone.count(fingers[4]):
                                    self.symmetrical_bones['fingers']['finger11'].append(bone)
                                    self.symmetrical_bones['fingers']['finger11'].sort()
                                    continue
                            if fingers[3]:
                                if bone.count(fingers[3]):
                                    self.symmetrical_bones['fingers']['finger1'].append(bone)
                                    self.symmetrical_bones['fingers']['finger1'].sort()
                                    continue

                            if fingers[8]:
                                if bone.count(fingers[8]):
                                    self.symmetrical_bones['fingers']['finger22'].append(bone)
                                    self.symmetrical_bones['fingers']['finger22'].sort()
                                    continue
                            if fingers[7]:
                                if bone.count(fingers[7]):
                                    self.symmetrical_bones['fingers']['finger21'].append(bone)
                                    self.symmetrical_bones['fingers']['finger21'].sort()
                                    continue
                            if fingers[6]:
                                if bone.count(fingers[6]):
                                    self.symmetrical_bones['fingers']['finger2'].append(bone)
                                    self.symmetrical_bones['fingers']['finger2'].sort()
                                    continue

                            if fingers[11]:
                                if bone.count(fingers[11]):
                                    self.symmetrical_bones['fingers']['finger32'].append(bone)
                                    self.symmetrical_bones['fingers']['finger32'].sort()
                                    continue
                            if fingers[10]:
                                if bone.count(fingers[10]):
                                    self.symmetrical_bones['fingers']['finger31'].append(bone)
                                    self.symmetrical_bones['fingers']['finger31'].sort()
                                    continue
                            if fingers[9]:
                                if bone.count(fingers[9]):
                                    self.symmetrical_bones['fingers']['finger3'].append(bone)
                                    self.symmetrical_bones['fingers']['finger3'].sort()
                                    continue

                            if fingers[14]:
                                if bone.count(fingers[14]):
                                    self.symmetrical_bones['fingers']['finger42'].append(bone)
                                    self.symmetrical_bones['fingers']['finger42'].sort()
                                    continue
                            if fingers[13]:
                                if bone.count(fingers[13]):
                                    self.symmetrical_bones['fingers']['finger41'].append(bone)
                                    self.symmetrical_bones['fingers']['finger41'].sort()
                                    continue
                            if fingers[12]:
                                if bone.count(fingers[12]):
                                    self.symmetrical_bones['fingers']['finger4'].append(bone)
                                    self.symmetrical_bones['fingers']['finger4'].sort()
                                    continue

                            custom_bones_raw.append(bone)

                ##Central bone##
                if central_bones_raw:
                    #Bone list order:
                    #spines = pelvis, spine, spine1, spine2, spine3, spine4
                    #head = neck, head

                    for bone in central_bones_raw:
                        if vatinfo.special_viewmodel:
                            spines = [None, None, None, None, 'Spine_2', 'Spine_3']
                            head = []
                        elif vatinfo.goldsource:
                            spines = ['Pelvis', 'Spine', 'Spine1', 'Spine2', 'Spine3', 'Spine4']
                            head = ['Neck', 'Head']

                        elif vatinfo.titanfall:
                            spines = ['Hip', 'Spinea', 'Spineb', 'Spinec', None, None]
                            head = ['Neck', 'Head']

                            if bone.title().count('Neckb'):
                                self.central_bones.setdefault('neck2', [])
                                self.central_bones['neck2'].append(bone)
                                self.central_bones['neck2'].sort()
                                continue

                        elif vatinfo.sbox:
                            spines = ['Pelvis', 'Spine_0', 'Spine_1', 'Spine_2', None, None]
                            head = ['Neck_0', 'Head']

                        else:
                            spines = ['Pelvis', 'Spine', 'Spine1', 'Spine2', 'Spine3', 'Spine4']
                            head = ['Neck', 'Head']

                        if spines:
                            if spines[0]:
                                if bone.title().count(spines[0]):
                                    self.central_bones['pelvis'].append(bone)
                                    self.central_bones['pelvis'].sort()
                                    continue

                            if spines[5]:
                                if bone.title().count(spines[5]):
                                    self.central_bones['spine4'].append(bone)
                                    self.central_bones['spine4'].sort()
                                    continue
                            if spines[4]:
                                if bone.title().count(spines[4]):
                                    self.central_bones['spine3'].append(bone)
                                    self.central_bones['spine3'].sort()
                                    continue
                            if spines[3]:
                                if bone.title().count(spines[3]):
                                    self.central_bones['spine2'].append(bone)
                                    self.central_bones['spine2'].sort()
                                    continue
                            if spines[2]:
                                if bone.title().count(spines[2]):
                                    self.central_bones['spine1'].append(bone)
                                    self.central_bones['spine1'].sort()
                                    continue
                            if spines[1]:
                                if bone.title().count(spines[1]):
                                    self.central_bones['spine'].append(bone)
                                    self.central_bones['spine'].sort()
                                    continue

                        if head:
                            if head[1]:
                                if bone.title().count(head[1]):
                                    self.central_bones['head'].append(bone)
                                    self.central_bones['head'].sort()
                                    continue
                            if head[0]:
                                if bone.title().count(head[0]):
                                    self.central_bones['neck'].append(bone)
                                    self.central_bones['neck'].sort()
                                    continue

                        self.custom_bones.setdefault(bone.casefold(), [])
                        self.custom_bones[bone.casefold()].append(bone)
                        self.custom_bones[bone.casefold()].sort()

                ##Helper bones##
                if helper_bones_raw:
                    for bone in helper_bones_raw:
                        #Bone list order:
                        #arms = Trapezius, Shoulder, Bicep, Elbow, Ulna, Wrist
                        #legs = Quadricep, Knee

                        #Additional bone set only in viewmodels that need a separate container to avoid messing with wrist generation
                        if vatinfo.viewmodel:
                            if bone.title().count('Ulna01'):
                                self.helper_bones['viewmodel']['ulna_extra1'].append(bone)
                                self.helper_bones['viewmodel']['ulna_extra1'].sort()
                                continue
                            elif bone.title().count('Ulna02'):
                                self.helper_bones['viewmodel']['ulna_extra2'].append(bone)
                                self.helper_bones['viewmodel']['ulna_extra2'].sort()
                                continue

                            elif bone.title().count('Wrist0'):
                                self.helper_bones['viewmodel']['wrist_extra'].append(bone)
                                self.helper_bones['viewmodel']['wrist_extra'].sort()
                                continue
                            elif bone.title().count('Wrist_Helper1'):
                                self.helper_bones['viewmodel']['wrist_helper1'].append(bone)
                                self.helper_bones['viewmodel']['wrist_helper1'].sort()
                                continue
                            elif bone.title().count('Wrist_Helper2'):
                                self.helper_bones['viewmodel']['wrist_helper2'].append(bone)
                                self.helper_bones['viewmodel']['wrist_helper2'].sort()
                                continue
                            
                            elif bone.title().count('Thumbroot'):
                                self.helper_bones['viewmodel']['thumbroot'].append(bone)
                                self.helper_bones['viewmodel']['thumbroot'].sort()
                                continue
                            elif bone.title().count('Thumb_Fix'):
                                self.helper_bones['viewmodel']['thumbfix'].append(bone)
                                self.helper_bones['viewmodel']['thumbfix'].sort()
                                continue

                        if vatinfo.titanfall:
                            arms = [None, 'Shouldertwist', 'Shouldermid', 'Elbowb', None, 'Forearm']
                            legs = [None, 'Kneeb']
                        elif vatinfo.sbox:
                            arms = [None, None, 'Arm_Upper', 'Arm_Elbow_Helper', None, 'Arm_Lower']
                            legs = ['Leg_Upper', 'Leg_Knee_Helper']

                            if bone.title().count('Leg_Lower'):
                                self.helper_bones['legs'].setdefault('lowerleg', [])
                                self.helper_bones['legs']['lowerleg'].append(bone)
                                self.helper_bones['legs']['lowerleg'].sort()
                                continue
                        else:
                            arms = ['Trap', 'Shoulder', 'Bicep', 'Elbow', 'Ulna', 'Wrist']
                            legs = ['Quad', 'Knee']

                        #Louis exclusive helper bone
                        if bone.title().count('Shoulder1'):
                            self.helper_bones['arms'].setdefault('shoulder1', [])
                            self.helper_bones['arms']['shoulder1'].append(bone)
                            self.helper_bones['arms']['shoulder1'].sort()
                            continue

                        if arms[0]:
                            if bone.title().count(arms[0]):
                                self.helper_bones['arms']['trapezius'].append(bone)
                                self.helper_bones['arms']['trapezius'].sort()
                                continue
                        if arms[1]:
                            if bone.title().count(arms[1]):
                                self.helper_bones['arms']['shoulder'].append(bone)
                                self.helper_bones['arms']['shoulder'].sort()
                                continue
                        if arms[2]:
                            if bone.title().count(arms[2]):
                                self.helper_bones['arms']['bicep'].append(bone)
                                self.helper_bones['arms']['bicep'].sort()
                                continue
                        if arms[3]:
                            if bone.title().count(arms[3]):
                                self.helper_bones['arms']['elbow'].append(bone)
                                self.helper_bones['arms']['elbow'].sort()
                                continue
                        if arms[4]:
                            if bone.title().count(arms[4]):
                                self.helper_bones['arms']['ulna'].append(bone)
                                self.helper_bones['arms']['ulna'].sort()
                                continue
                        if arms[5]:
                            if bone.title().count(arms[5]):
                                self.helper_bones['arms']['wrist'].append(bone)
                                self.helper_bones['arms']['wrist'].sort()
                                continue

                        if legs[0]:
                            if bone.title().count(legs[0]):
                                self.helper_bones['legs']['quadricep'].append(bone)
                                self.helper_bones['legs']['quadricep'].sort()
                                continue
                        if legs[1]:
                            if bone.title().count(legs[1]):
                                self.helper_bones['legs']['knee'].append(bone)
                                self.helper_bones['legs']['knee'].sort()
                                continue
                        
                        #Creates pairs for helper bones that aren't the conventional
                        prefix, bone2 = bone_convert(bone)

                        if bone2.title().startswith(self.side[0]):
                            self.helper_bones['others'].setdefault(bone2.title().replace(self.side[0], '').casefold(), [])
                            self.helper_bones['others'][bone2.title().replace(self.side[0], '').casefold()].append(bone)
                            self.helper_bones['others'][bone2.title().replace(self.side[0], '').casefold()].sort()
                        elif bone2.title().endswith(self.side[2]):
                            self.helper_bones['others'].setdefault(bone2.title().replace(self.side[2], '').casefold(), [])
                            self.helper_bones['others'][bone2.title().replace(self.side[2], '').casefold()].append(bone)
                            self.helper_bones['others'][bone2.title().replace(self.side[2], '').casefold()].sort()
                        elif bone2.title().startswith('Left_'):
                            self.helper_bones['others'].setdefault(bone.title().replace('Left_', '').casefold(), [])
                            self.helper_bones['others'][bone.title().replace('Left_', '').casefold()].append(bone)
                            self.helper_bones['others'][bone.title().replace('Left_', '').casefold()].sort()
                        elif bone2.title().endswith('_Left'):
                            self.helper_bones['others'].setdefault(bone.title().replace('_Left', '').casefold(), [])
                            self.helper_bones['others'][bone.title().replace('_Left', '').casefold()].append(bone)
                            self.helper_bones['others'][bone.title().replace('_Left', '').casefold()].sort()

                        elif bone2.title().startswith(self.side[1]):
                            self.helper_bones['others'].setdefault(bone2.title().replace(self.side[1], '').casefold(), [])
                            self.helper_bones['others'][bone2.title().replace(self.side[1], '').casefold()].append(bone)
                            self.helper_bones['others'][bone2.title().replace(self.side[1], '').casefold()].sort()
                        elif bone2.title().endswith(self.side[3]):
                            self.helper_bones['others'].setdefault(bone2.title().replace(self.side[3], '').casefold(), [])
                            self.helper_bones['others'][bone2.title().replace(self.side[3], '').casefold()].append(bone)
                            self.helper_bones['others'][bone2.title().replace(self.side[3], '').casefold().casefold()].sort()
                        elif bone2.title().startswith('Right_'):
                            self.helper_bones['others'].setdefault(bone.title().replace('Right_', '').casefold(), [])
                            self.helper_bones['others'][bone.title().replace('Right_', '').casefold()].append(bone)
                            self.helper_bones['others'][bone.title().replace('Right_', '').casefold()].sort()
                        elif bone2.title().endswith('_Right'):
                            self.helper_bones['others'].setdefault(bone.title().replace('_Right', '').casefold(), [])
                            self.helper_bones['others'][bone.title().replace('_Right', '').casefold()].append(bone)
                            self.helper_bones['others'][bone.title().replace('_Right', '').casefold()].sort()
                        else:
                            self.helper_bones['others']['others'].append(bone)
                            self.helper_bones['others']['others'].sort()

                ##Other bones##
                if other_bones_raw:
                    for bone in other_bones_raw:
                        #Titanfall
                        if vatinfo.titanfall:
                            if bone.count('ja'):
                                self.other_bones['attachment'].append(bone)
                                self.other_bones['attachment'].sort()

                            elif bone.startswith('jx'):
                                self.other_bones['others'].append(bone)
                                self.other_bones['others'].sort()
                            else:
                                custom_bones_raw.append(bone)
                        elif vatinfo.sbox:
                            if bone.casefold().count('ik'):
                                self.other_bones.setdefault('ik', [])
                                self.other_bones['ik'].append(bone)
                                self.other_bones['ik'].sort()
                        else:
                            if bone.title().count('Forward'):
                                self.other_bones['forward'].append(bone)
                                self.other_bones['forward'].sort()

                            elif bone.title().count('Weapon') or bone.title().count('Muzzle') or bone.title().count('Shell'):
                                self.other_bones['weapon'].append(bone)
                                self.other_bones['weapon'].sort()

                            elif bone.startswith('a1.') or bone.startswith('a2.'):
                                self.other_bones['attachment'].append(bone)
                                self.other_bones['attachment'].sort()

                            elif bone.title().count('Bip01'):
                                self.central_bones['pelvis'].append(bone)
                                self.central_bones['pelvis'].sort()

                            elif bone.title().count('Camera'):
                                self.other_bones['viewmodel'].append(bone)
                                self.other_bones['viewmodel'].sort()

                            elif bone.title().count('Jiggle') or bone.title().count('Jiggy'):
                                self.custom_bones['jiggle'].append(bone)
                                self.custom_bones['jiggle'].sort()

                            else:
                                self.other_bones['others'].append(bone)
                                self.other_bones['others'].sort()

                ##Custom bones##
                if custom_bones_raw:
                    for bone in custom_bones_raw:
                        if bone.title().count('Jiggle'):
                            self.custom_bones['jiggle'].append(bone)
                            self.custom_bones['jiggle'].sort()

                        elif bone.title().startswith(self.side[0]):
                            self.custom_bones.setdefault(bone.title().replace(self.side[0], '').casefold(), [])
                            self.custom_bones[bone.title().replace(self.side[0], '').casefold()].append(bone)
                            self.custom_bones[bone.title().replace(self.side[0], '').casefold()].sort()
                        elif bone.title().endswith(self.side[2]):
                            self.custom_bones.setdefault(bone.title().replace(self.side[2], '').casefold(), [])
                            self.custom_bones[bone.title().replace(self.side[2], '').casefold()].append(bone)
                            self.custom_bones[bone.title().replace(self.side[2], '').casefold()].sort()
                        elif bone.title().startswith('Left_'):
                            self.custom_bones.setdefault(bone.title().replace('Left_', '').casefold(), [])
                            self.custom_bones[bone.title().replace('Left_', '').casefold()].append(bone)
                            self.custom_bones[bone.title().replace('Left_', '').casefold()].sort()
                        elif bone.title().endswith('_Left'):
                            self.custom_bones.setdefault(bone.title().replace('_Left', '').casefold(), [])
                            self.custom_bones[bone.title().replace('_Left', '').casefold()].append(bone)
                            self.custom_bones[bone.title().replace('_Left', '').casefold()].sort()

                        elif bone.title().startswith(self.side[1]):
                            self.custom_bones.setdefault(bone.title().replace(self.side[1], '').casefold(), [])
                            self.custom_bones[bone.title().replace(self.side[1], '').casefold()].append(bone)
                            self.custom_bones[bone.title().replace(self.side[1], '').casefold()].sort()
                        elif bone.title().endswith(self.side[3]):
                            self.custom_bones.setdefault(bone.title().replace(self.side[3], '').casefold(), [])
                            self.custom_bones[bone.title().replace(self.side[3], '').casefold()].append(bone)
                            self.custom_bones[bone.title().replace(self.side[3], '').casefold()].sort()
                        elif bone.title().startswith('Right_'):
                            self.custom_bones.setdefault(bone.title().replace('Right_', '').casefold(), [])
                            self.custom_bones[bone.title().replace('Right_', '').casefold()].append(bone)
                            self.custom_bones[bone.title().replace('Right_', '').casefold()].sort()
                        elif bone.title().endswith('_Right'):
                            self.custom_bones.setdefault(bone.title().replace('_Right', '').casefold(), [])
                            self.custom_bones[bone.title().replace('_Right', '').casefold()].append(bone)
                            self.custom_bones[bone.title().replace('_Right', '').casefold()].sort()
                        else:
                            self.custom_bones['others'].append(bone)
                            self.custom_bones['others'].sort()

                ##Creates empty pairs for single bones##
                for cat in self.symmetrical_bones.keys():
                    for container in self.symmetrical_bones[cat].keys():
                        if len(self.symmetrical_bones[cat][container]) == 1:
                            bone = self.symmetrical_bones[cat][container][0]
                            prefix, bone = bone_convert(bone)

                            if bone.title().startswith(self.side[0]) or bone.title().endswith(self.side[2]):
                                self.symmetrical_bones[cat][container].insert(1, None)

                            elif bone.title().startswith(self.side[1]) or bone.title().endswith(self.side[3]):
                                self.symmetrical_bones[cat][container].insert(0, None)

                for cat in self.helper_bones.keys():
                    for container in self.helper_bones[cat].keys():
                        if len(self.helper_bones[cat][container]) == 1:
                            bone = self.helper_bones[cat][container][0]
                            prefix, bone = bone_convert(bone)

                            if bone.title().startswith(self.side[0]) or bone.title().endswith(self.side[2]):
                                self.helper_bones[cat][container].insert(1, None)
                            elif bone.title().startswith(self.side[1]) or bone.title().endswith(self.side[3]):
                                self.helper_bones[cat][container].insert(0, None)
                            else: #Nick left wrist fix
                                self.helper_bones[cat][container].insert(1, None)

                if len(self.helper_bones['arms']['wrist']) == 2:
                    #Position fix for Nick's left wrist
                    if self.helper_bones['arms']['wrist'][1] == 'h2.wrist':
                        self.helper_bones['arms']['wrist'].sort(reverse=True)

                for bone in self.full_bonelist:
                    bone = armature.pose.bones[bone]
                    if bone.bone.use_connect:
                        vatinfo.unconverted_armature = True
                        break

                #Final bone report
                if report:
                    print("Symmetrical bones:", list(self.symmetrical_bones.values()))
                    print("Central bones:", list(self.central_bones.values()))
                    print("Helper bones:", list(self.helper_bones.values()))
                    print("Other bones:", list(self.other_bones.values()))
                    print("Custom bones:", self.custom_bones)
                
            else:
                vatinfo.scheme = -1

            #print(symmetrical_bones_raw)
            #print(central_bones_raw)
            #print(helper_bones_raw)
            #print(other_bones_raw)
            #print(custom_bones_raw)

    ##Relative unit##
    def get_unit(self):
        vatinfo = bpy.context.scene.vatinfo 

        #Equivalent to 1 meter relative to the first bone's length in order to maintain consistency between different scales
        if not vatinfo.unit:
            armature = self.armature
            unit_bone = armature.pose.bones[0].length

            #if vatinfo.goldsource:
            #    vatinfo.unit = unit_bone*209.97500305553845
            if vatinfo.goldsource:
                vatinfo.unit = unit_bone*4.36085145847641
            elif vatinfo.sbox:
                vatinfo.unit = unit_bone*0.09201296705261927
            else:
                vatinfo.unit = unit_bone*5.356327005986801

            print('Relative unit:', vatinfo.unit)

        #Unit relative to the size it would be if imported from Blender Source Tools for Source armatures (For the sake of readability)

    def get_armatures(self): #Gets generated armatures for selected armature
        vatinfo = bpy.context.scene.vatinfo

        def get_weight_armature():
            try:
                self.weight_armature = bpy.data.objects[self.armature.name + '.weight']
                vatinfo.weight_armature = True
            except:
                vatinfo.weight_armature = False
        
            try:
                self.weight_armature_real = bpy.data.armatures[self.armature_real.name + '.weight']
                vatinfo.weight_armature = True
            except:
                vatinfo.weight_armature = False
                
        def get_anim_armature():
            #Checks if it's a setup armature or a proper armature
            try:
                try:
                    self.animation_armature = bpy.data.objects[self.armature.name + '.anim_setup']
                    vatinfo.animation_armature_setup = True
                except:
                    self.animation_armature = bpy.data.objects[self.armature.name + '.anim']
                    vatinfo.animation_armature_setup = False

                try:
                    self.animation_armature_real = bpy.data.armatures[self.armature_real.name + '.anim_setup']
                    vatinfo.animation_armature_setup = True
                except:
                    self.animation_armature_real = bpy.data.armatures[self.armature_real.name + '.anim']
                    vatinfo.animation_armature_setup = False

                vatinfo.animation_armature = True

            except:
                vatinfo.animation_armature = False

        get_weight_armature()
        get_anim_armature()

    def get_constraints(self): #Gets previously added constraints that have not been removed

        vatinfo = bpy.context.scene.vatinfo
        armature = self.armature

        for cat in self.symmetrical_bones.keys():
            for bone in self.symmetrical_bones[cat].values():
                for bone in bone:
                    if bone:
                        if vatinfo.symmetry:
                            break
                        else:
                            prefix, bone = bone_convert(bone)
                            if bone.startswith(self.side[0]) or bone.endswith(self.side[2]):
                                for constraint in armature.pose.bones[prefix + bone].constraints:
                                    if constraint.name == 'Constraint Symmetry Location' or constraint.name == 'Constraint Symmetry Rotation':
                                        vatinfo.symmetry = 1
                                        break
                                    else:
                                        vatinfo.symmetry = 0

                            elif bone.startswith(self.side[1]) or bone.endswith(self.side[3]):
                                for constraint in armature.pose.bones[prefix + bone].constraints:
                                    if constraint.name == 'Constraint Symmetry Location' or constraint.name == 'Constraint Symmetry Rotation':
                                        vatinfo.symmetry = 2
                                        break
                                    else:
                                        vatinfo.symmetry = 0
        
        for cat in self.helper_bones.keys():
            for bone in self.helper_bones[cat].values():
                for bone in bone:
                    if bone:
                        if vatinfo.symmetry:
                            break
                        else:
                            prefix, bone = bone_convert(bone)
                            if bone.startswith(self.side[0]) or bone.endswith(self.side[2]):
                                for constraint in armature.pose.bones[prefix + bone].constraints:
                                    if constraint.name == 'Constraint Symmetry Location' or constraint.name == 'Constraint Symmetry Rotation':
                                        vatinfo.symmetry = 1
                                        break
                                    else:
                                        vatinfo.symmetry = 0

                            elif bone.startswith(self.side[1]) or bone.endswith(self.side[3]):
                                for constraint in armature.pose.bones[prefix + bone].constraints:
                                    if constraint.name == 'Constraint Symmetry Location' or constraint.name == 'Constraint Symmetry Rotation':
                                        vatinfo.symmetry = 2
                                        break
                                    else:
                                        vatinfo.symmetry = 0
            
    def set_groups(self): #Organizes bones by bone group and bone layers
        armature = self.armature

        #Checks if any groups exist already
        group = armature.pose.bone_groups.keys()

        if not group:
            #Creates groups and sets their color
            for group, color in zip(['Center', 'Left Arm', 'Right Arm', 'Left Leg', 'Right Leg', 'Helpers', 'Attachments', 'Weapon', 'Others', 'Custom'], ['THEME03', 'THEME01', 'THEME04', 'THEME01', 'THEME04', 'THEME09', 'THEME14', 'THEME07', 'THEME10', 'THEME06']):
                armature.pose.bone_groups.new(name=group)
                armature.pose.bone_groups[group].color_set = color
                
            
            for cat in self.symmetrical_bones.keys():
                #Arms and fingers
                if cat == 'arms' or cat == 'fingers':
                    for bone in self.symmetrical_bones[cat].values():
                        for index, bone in enumerate(bone):
                            if bone:
                                prefix, bone = bone_convert(bone)
                                if index == 0:
                                    armature.pose.bones[prefix + bone].bone_group_index = 1
                                    armature.data.bones[prefix + bone].layers[1] = True

                                elif index == 1:
                                    armature.pose.bones[prefix + bone].bone_group_index = 2
                                    armature.data.bones[prefix + bone].layers[2] = True

                                armature.data.bones[prefix + bone].layers[0] = False

                #Legs
                elif cat == 'legs':
                    for bone in self.symmetrical_bones[cat].values():
                        for index, bone in enumerate(bone):
                            if bone:
                                prefix, bone = bone_convert(bone)
                                if index == 0:
                                    armature.pose.bones[prefix + bone].bone_group_index = 3
                                    armature.data.bones[prefix + bone].layers[3] = True
                                    
                                elif index == 1:
                                    armature.pose.bones[prefix + bone].bone_group_index = 4
                                    armature.data.bones[prefix + bone].layers[4] = True

                                armature.data.bones[prefix + bone].layers[0] = False
                    
            for bone in self.central_bones.values():
                for bone in bone:
                    if bone:
                        prefix, bone = bone_convert(bone)
                        
                        armature.pose.bones[prefix + bone].bone_group_index = 0

            if self.helper_bones:
                for cat in self.helper_bones.keys():
                    for bone in self.helper_bones[cat].values():
                        for bone in bone:
                            if bone:
                                prefix, bone = bone_convert(bone)

                                armature.pose.bones[prefix + bone].bone_group_index = 5
                                armature.data.bones[prefix + bone].layers[5] = True
                                armature.data.bones[prefix + bone].layers[0] = False

    
            for container, bone in self.other_bones.items():
                for bone in bone:
                    if bone:
                        prefix, bone = bone_convert(bone)
                        if container == 'attachment':
                            armature.pose.bones[prefix + bone].bone_group_index = 6
                            armature.data.bones[prefix + bone].layers[6] = True
                            armature.data.bones[prefix + bone].layers[0] = False
                        elif container == 'weapon':
                            armature.pose.bones[prefix + bone].bone_group_index = 7
                            armature.data.bones[prefix + bone].layers[7] = True
                            armature.data.bones[prefix + bone].layers[0] = False
                        else:
                            armature.pose.bones[prefix + bone].bone_group_index = 8
                            armature.data.bones[prefix + bone].layers[8] = True
                            armature.data.bones[prefix + bone].layers[0] = False
                    
            #Custom bones
            for bone in self.custom_bones.values():
                for bone in bone:
                    if bone:
                        prefix, bone = bone_convert(bone)

                        armature.pose.bones[prefix + bone].bone_group_index = 9
                        armature.data.bones[prefix + bone].layers[9] = True
                        armature.data.bones[prefix + bone].layers[0] = False

            #Reveals used layers
            for i in [0,1,2,3,4,5,6,7,8, 9]:
                armature.data.layers[i] = True

            print("Bone groups set!")
            
    def set_helper_bones(self):
        vatproperties = bpy.context.scene.vatproperties
        vatinfo = bpy.context.scene.vatinfo
        armature = self.armature
        new = False

        for cat in self.helper_bones.keys():
            for container, bone in self.helper_bones[cat].items():
                if container == 'wrist' or container == 'ulna' or container == 'elbow' or container == 'knee' or container == 'quadricep' or container == 'shoulder' or container == 'thumbroot' or container == 'forearm_driven':
                    for index, bone in enumerate(bone):
                        if bone:
                            if index > 1:
                                break
                            prefix, bone = bone_convert(bone)
                            
                            #Adds transforms to only these helper bones unless already existing
                            try:
                                armature.pose.bones[prefix + bone].constraints['Procedural Bone']
                            except:
                                transform = armature.pose.bones[prefix + bone].constraints.new('TRANSFORM')
                                new = True

                                #Initial parameters
                                transform.name = "Procedural Bone"
                                transform.target = self.armature
                                transform.map_from = 'ROTATION'
                                transform.map_to = 'ROTATION'
                                transform.target_space = 'LOCAL'
                                transform.owner_space = 'LOCAL'
                            
                                #Hand rotation
                                if container == 'wrist' or container == 'ulna' or container == 'forearm_driven':
                                    if vatinfo.special_viewmodel:
                                        transform.from_min_y_rot = radians(-90)
                                        transform.from_max_y_rot = radians(90)
                                    else:
                                        transform.from_min_x_rot = radians(-90)
                                        transform.from_max_x_rot = radians(90)

                                    prefix, bone = bone_convert(self.symmetrical_bones['arms']['hand'][index])
                                    transform.subtarget = prefix + bone

                                    if container == 'wrist':
                                        transform.to_min_x_rot = radians(-75)
                                        transform.to_max_x_rot = radians(75)

                                    elif container == 'ulna':
                                        if vatinfo.special_viewmodel:
                                            transform.to_min_y_rot = radians(-50)
                                            transform.to_max_y_rot = radians(50)
                                        else:
                                            transform.to_min_x_rot = radians(-50)
                                            transform.to_max_x_rot = radians(50)

                                    elif container == 'forearm_driven':
                                        transform.to_min_x_rot = radians(-25)
                                        transform.to_max_x_rot = radians(20)

                                #Forearm and thigh rotation
                                elif container == 'elbow' or container == 'knee' or container == 'quadricep':
                                    if vatinfo.titanfall and container == 'elbow':
                                        transform.from_min_y_rot = radians(-90)
                                        transform.from_max_y_rot = radians(90)

                                        transform.to_min_y_rot = radians(-45)
                                        transform.to_max_y_rot = radians(45)
                                    else:
                                        transform.from_min_z_rot = radians(-90)
                                        transform.from_max_z_rot = radians(90)

                                        transform.to_min_z_rot = radians(-45)
                                        transform.to_max_z_rot = radians(45)
                                    
                                    if container == 'elbow':
                                        prefix, bone = bone_convert(self.symmetrical_bones['arms']['forearm'][index])
                                        transform.subtarget = prefix + bone

                                    elif container == 'knee':
                                        prefix, bone = bone_convert(self.symmetrical_bones['legs']['calf'][index])
                                        transform.subtarget = prefix + bone

                                    elif container == 'quadricep':
                                        if not vatinfo.sbox:
                                            prefix, bone = bone_convert(self.symmetrical_bones['legs']['thigh'][index])
                                            transform.subtarget = prefix + bone

                                elif container == 'shoulder':
                                    #Not for Titanfall characters
                                    if not vatinfo.titanfall:
                                        transform.from_min_y_rot = radians(-45)
                                        transform.from_max_y_rot = radians(45)

                                        #Nick exclusive
                                        if self.helper_bones['arms']['wrist'] and self.helper_bones['arms']['wrist'][0] == 'h2.wrist':
                                            transform.to_min_y_rot = radians(45)
                                            transform.to_max_y_rot = radians(-45)
                                        else:
                                            transform.to_min_y_rot = radians(5)
                                            transform.to_max_y_rot = radians(-5)

                                        prefix, bone = bone_convert(self.symmetrical_bones['arms']['upperarm'][index])
                                        transform.subtarget = prefix + bone

                                elif container == 'thumbroot':
                                    transform.from_min_y_rot = radians(-45)
                                    transform.from_max_y_rot = radians(45)

                                    transform.from_min_z_rot = radians(-75)
                                    transform.from_max_z_rot = radians(75)

                                    if index == 0:
                                        transform.to_min_y_rot = radians(30)
                                        transform.to_max_y_rot = radians(-30)
                                    else:
                                        transform.to_min_y_rot = radians(-30)
                                        transform.to_max_y_rot = radians(30)

                                    transform.to_min_z_rot = radians(-45)
                                    transform.to_max_z_rot = radians(45)

                                    prefix, bone = bone_convert(self.symmetrical_bones['fingers']['finger0'][index])
                                    transform.subtarget = prefix + bone
        if new:
            print("Procedural bones configured!")

        if vatinfo.viewmodel:
            vatproperties.bake_helper_bones = True
        else:
            vatproperties.bake_helper_bones = False

#Some functions (Namely creating new bones) do not add the newly created info to the object data until a mode change occurs at least once
def update(type, object=None):
    if type == 0: #Simple update, used for making new bones show up in data
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
    elif type == 1 and object: #Used to work with edit_bones, since it's not possible to use in anything other than edit mode
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT') #You're required to be in edit mode to use 'data.edit_bones', else there will be no bone info given.
        object.select_set(True)
        bpy.context.view_layer.objects.active = object
        bpy.ops.object.mode_set(mode='EDIT')

def convert_armature_to_source():
    vatproperties = bpy.context.scene.vatproperties
    pass

def generate_armature(type, action): #Creates or deletes the weight armature
    vatinfo = bpy.context.scene.vatinfo
    
    real_armature = bpy.data.armatures[arm.armature_real.name]
    
    unit = vatinfo.unit

    #Creation
    if action == 0:

        #Weight armature datablock
        if type == 'weight':
            arm.weight_armature_real = real_armature.copy()
            arm.weight_armature_real.name = arm.armature_real.name + '.weight'

            #Creation and link to current scene
            arm.weight_armature = bpy.data.objects.new(arm.armature.name + '.weight', arm.weight_armature_real)
            vatinfo.weight_armature = True

            collection = arm.armature.users_collection[0]
            collection.objects.link(arm.weight_armature)

            armature = arm.weight_armature
            
        #Animation armature datablock
        elif type == 'anim':
            arm.animation_armature_real = real_armature.copy()
            arm.animation_armature_real.name = arm.armature_real.name + '.anim_setup'

            #Creation and link to current scene
            arm.animation_armature = bpy.data.objects.new(arm.armature.name + '.anim_setup', arm.animation_armature_real)
            vatinfo.animation_armature = True

            collection = arm.armature.users_collection[0]
            collection.objects.link(arm.animation_armature)

            armature = arm.animation_armature
        
        #Focuses on newly created armature
        update(1, armature)

        ##Unimportant bone removal##

        #Removes bones such as weapon or attachment bones
        if arm.other_bones:
            for container, bone in arm.other_bones.items():
                for bone in bone:
                    if bone:
                        if container == 'forward' or container == 'root' or container == 'ik' or bone == 'p2.ValveBiped':
                            prefix, bone = bone_convert(bone)
                            bone = armature.data.edit_bones[prefix + bone]
                            armature.data.edit_bones.remove(bone)

                        elif type == 'weight':
                            prefix, bone = bone_convert(bone)

                            bone = armature.data.edit_bones[prefix + bone]
                            armature.data.edit_bones.remove(bone)

        #Keeps only the bare minimum bones for Rigify
        if type == 'anim':
            for cat in arm.helper_bones.keys():
                for container, bone in arm.helper_bones[cat].items():
                    for bone in bone:
                        if bone:
                            prefix, bone = bone_convert(bone)
                            ebone = armature.data.edit_bones[prefix + bone]
                        
                            armature.data.edit_bones.remove(ebone)

        elif type == 'weight':
            #Removes wrist helpers for viewmodels since i've never seen them used for anything and they mess with weight generation
            for container, bone in arm.helper_bones['viewmodel'].items():
                if container != 'thumbroot' and container != 'forearm_driven':
                    for bone in bone:
                        if bone:
                            prefix, bone = bone_convert(bone)
                            ebone = armature.data.edit_bones[prefix + bone]
                        
                            armature.data.edit_bones.remove(ebone)
                            
        ##Setup for armatures, tweaking bone positions and the like##

        arm.chainless_bones = []
        arm.chain_start = []

        #Temporal list with prefixes taken out
        custom_bones = []

        for cat in arm.custom_bones.keys():
            for bone in arm.custom_bones[cat]:
                if bone:
                    prefix, bone = bone_convert(bone)
                    
                    custom_bones.append(bone)

        #Custom bones, placed first so changes to the standard bones by them are overwritten later
        for cat in arm.custom_bones.keys():
            for bone in arm.custom_bones[cat]:
                if bone:
                    prefix, bone2 = bone_convert(bone)
                    ebone = armature.data.edit_bones[prefix + bone2]
                    pbone = armature.pose.bones[prefix + bone2]

                    marked = False

                    if ebone.parent:
                        parent = ebone.parent.name
                    
                        if custom_bones.count(parent.replace(prefix, '')):
                            marked = True

                        parent = ebone.parent
                        #If bone's parent is not any of the default ones
                        if marked:
                            #Avoids Blender deleting the bone if the connection causes the child bone to have virtually 0 length
                            if ebone.tail != parent.tail and ebone.head != parent.head:
                                parent.tail = pbone.head

                            #Straightens the first bone of a line
                            if not ebone.children:
                                length = parent.length
                                parent.length = parent.length*2
                                ebone.tail = parent.tail
                                parent.length = length
                            
                            if len(parent.children) < 2:
                                ebone.use_connect = True

                            if not ebone.use_connect and ebone.children:
                                arm.chain_start.append(bone)
                        else:
                            if not ebone.children:
                                arm.chainless_bones.append(bone)
                                if ebone.length < 0.3*unit:
                                    pbone.rotation_quaternion[3] = -1
                                    pbone.scale = 5,5,5

                            if not ebone.use_connect and ebone.children:
                                if type == 'anim':
                                    pbone.rigify_type = 'basic.super_copy'
                                    pbone.rigify_parameters.super_copy_widget_type = 'bone'

                                #arm.chain_start.append(bone)

        #Isolated bones for the custom bones
        if type == 'anim':
            for cat in arm.custom_bones.keys():
                for bone in arm.custom_bones[cat]:
                    if bone:
                        prefix, bone2 = bone_convert(bone)
                        ebone = armature.data.edit_bones[prefix + bone2]
                        pbone = armature.pose.bones[prefix + bone2]

                        #Creates copy of bone that retains the original rotation for the retarget empties
                        isolatedbone = armature.data.edit_bones.new(prefix + bone2 + ".isolated")
                        isolatedbone.head = armature.pose.bones[prefix + bone2].head
                        isolatedbone.tail = armature.pose.bones[prefix + bone2].tail
                        isolatedbone.roll = armature.data.edit_bones[prefix + bone2].roll
                        isolatedbone.parent = armature.data.edit_bones[prefix + bone2]
                        isolatedbone.use_deform = False
                        isolatedbone.layers[28] = True

                        for i in range(0, 11):
                            isolatedbone.layers[i] = False

        #Symmetrical bones
        for cat in arm.symmetrical_bones.keys():
            for container, bone in arm.symmetrical_bones[cat].items():
                for index, bone in enumerate(bone):
                    if bone:
                        prefix, bone = bone_convert(bone)
                        if type == 'anim':
                            #Creates copy of bone that retains the original rotation for the retarget empties
                            if vatinfo.scheme == 0 and not vatinfo.sbox:
                                bone2 = armature_rename.bone_rename(1, bone, index)
                                isolatedbone = armature.data.edit_bones.new(prefix + bone2 + ".isolated")
                            else:
                                isolatedbone = armature.data.edit_bones.new(prefix + bone + ".isolated")
                            isolatedbone.head = armature.pose.bones[prefix + bone].head
                            isolatedbone.tail = armature.pose.bones[prefix + bone].tail
                            isolatedbone.roll = armature.data.edit_bones[prefix + bone].roll
                            isolatedbone.use_deform = False
                            isolatedbone.layers[28] = True
                            for i in range(0, 11):
                                isolatedbone.layers[i] = False

                        ebone = armature.data.edit_bones[prefix + bone]
                        pbone = armature.pose.bones[prefix + bone]
                        parent = ebone.parent

                        if arm.central_bones['pelvis']:
                            prefix, bone = bone_convert(arm.central_bones['pelvis'][0])
                            if parent.name == prefix + bone:
                                continue
                            else:
                                parent.tail = pbone.head
                        else:
                            parent.tail = pbone.head
                        
                        #Filters out bones whose parent should not be connected to them
                        if container == 'thigh' or container == 'clavicle' or container == 'finger0' or container == 'finger1' or container == 'finger2' or container == 'finger3' or container == 'finger4' or container == 'fingercarpal' or container == 'indexmeta' or container == 'middlemeta' or container == 'ringmeta':
                            continue
                        else:
                            if type == 'weight':
                                if container == 'calf' or container == 'upperarm' or container == 'forearm' or container == 'hand':
                                    continue
                                elif vatinfo.sbox and container == 'foot':
                                    continue
                                
                        ebone.use_connect = True

        #Helper bones tweak if weight armature
        if type == 'weight':
            for cat in arm.helper_bones.keys():
                for container, bone in arm.helper_bones[cat].items():
                    for bone in bone:
                        if bone:
                            if container.count('thumb') or container.count('wrist') or container.count('ulna') or container.count('forearm'):
                                continue
                            
                            prefix, bone = bone_convert(bone)
                            pbone = armature.pose.bones[prefix + bone]
                            ebone = armature.data.edit_bones[prefix + bone]
                            parent = armature.data.edit_bones[prefix + bone].parent

                            if cat != 'others':
                                parent.tail = pbone.head

                            #Filters out bones whose parent should not be connected to them
                            if container == 'knee' or container == 'elbow' or container == 'quadricep' or container == 'bicep' or container == 'shoulder' or cat == 'others':
                                continue
                            else:
                                ebone.use_connect = True

        #Central bones
        for container, bone in arm.central_bones.items():
            for index, bone in enumerate(bone):
                if bone:
                    prefix, bone = bone_convert(bone)

                    if type == 'anim':
                        #Creates copy of bone that retains the original rotation for the retarget empties
                        isolatedbone = armature.data.edit_bones.new(prefix + bone + ".isolated")
                        isolatedbone.head = armature.pose.bones[prefix + bone].head
                        isolatedbone.tail = armature.pose.bones[prefix + bone].tail
                        isolatedbone.roll = armature.data.edit_bones[prefix + bone].roll
                        isolatedbone.parent = armature.data.edit_bones[prefix + bone]
                        isolatedbone.use_deform = False
                        isolatedbone.layers[28] = True

                        for i in range(0, 11):
                            isolatedbone.layers[i] = False
                    
                    pbone = armature.pose.bones[prefix + bone]
                    ebone = armature.data.edit_bones[prefix + bone]

                    #No parent
                    if container != 'pelvis':
                        if armature.data.edit_bones[prefix + bone].parent:
                            parent = armature.data.edit_bones[prefix + bone].parent

                            if arm.central_bones['pelvis']:
                                prefix, bone = bone_convert(arm.central_bones['pelvis'][0])
                                if parent.name == prefix + bone and container != 'spine':
                                    continue
                                else:
                                    parent.tail = pbone.head
                            else:
                                parent.tail = pbone.head

                            #Neck should not be connected to its parent
                            if container.count('neck') == 0:
                                ebone.use_connect = True

                    #Extends head's length to be on par with actual head height
                    if container == 'head':
                        if vatinfo.goldsource: #Update the remaining 2 to *unit
                            ebone.tail.xyz = pbone.head.x, pbone.head.y, pbone.head.z + 10*unit
                        elif vatinfo.sbox:
                            ebone.tail.xyz = pbone.head.x, pbone.head.y, pbone.head.z + 35*unit
                        else:
                            ebone.tail.xyz = pbone.head.x, pbone.head.y, pbone.head.z + 6*unit

        if type == 'anim':
            for container, bone in arm.other_bones.items():
                if container == 'weapon' or container == 'viewmodel':
                    for bone in bone:
                        if bone:
                            if container == 'weapon' or bone.title().count('Camera'):
                                prefix, bone = bone_convert(bone)
                                #Creates copy of bone that retains the original rotation for the retarget empties
                                isolatedbone = armature.data.edit_bones.new(prefix + bone + ".isolated")
                                isolatedbone.head = armature.pose.bones[prefix + bone].head
                                isolatedbone.tail = armature.pose.bones[prefix + bone].tail
                                isolatedbone.roll = armature.data.edit_bones[prefix + bone].roll
                                isolatedbone.parent = armature.data.edit_bones[prefix + bone]
                                isolatedbone.use_deform = False
                                isolatedbone.layers[28] = True

                                for i in range(0, 11):
                                    isolatedbone.layers[i] = False
            
        ##Bone tweaks##

        #Extends toe tip to be where the actual tip should be
        for index, bone in enumerate(arm.symmetrical_bones['legs']['toe0']):
            if bone:
                prefix, bone = bone_convert(bone)
                etoe = armature.data.edit_bones[prefix + bone]
                ptoe = armature.pose.bones[prefix + bone]

                if arm.symmetrical_bones['legs'].get('toe01') and arm.symmetrical_bones['legs']['toe01'][index]:
                    prefix, bone = bone_convert(arm.symmetrical_bones['legs']['toe01'][index])
                    etoe01 = armature.data.edit_bones[prefix + bone]

                    if arm.symmetrical_bones['legs'].get('toe02') and arm.symmetrical_bones['legs']['toe02'][index]:
                        prefix, bone = bone_convert(arm.symmetrical_bones['legs']['toe02'][index])
                        etoe02 = armature.data.edit_bones[prefix + bone]

                        length = etoe01.length
                        etoe01.length = etoe01.length*1.25

                        etoe02.tail = etoe01.tail

                        etoe01.length = length
                    else:
                        length = etoe.length
                        etoe.length = etoe.length*1.25

                        etoe01.tail = etoe.tail

                        etoe.length = length
                else:
                    if vatinfo.sbox:
                        armature.data.edit_bones[prefix + bone].tail.xyz = ptoe.head.x, -8*unit, ptoe.head.z
                    elif arm.symmetrical_bones['legs'].get('thighlow'):
                        armature.data.edit_bones[prefix + bone].tail.xyz = ptoe.head.x*1.1, -2*unit, ptoe.head.z
                    else:
                        armature.data.edit_bones[prefix + bone].tail.xyz = ptoe.head.x*1.1, -7*unit, ptoe.head.z

        #Extends hand bone
        for index, bone in enumerate(arm.symmetrical_bones['arms']['hand']):
            if bone:
                prefix, bone = bone_convert(bone)
                ehand = armature.data.edit_bones[prefix + bone]

                if arm.symmetrical_bones['arms']['forearm'] and arm.symmetrical_bones['arms']['forearm'][index]:
                    prefix, bone = bone_convert(arm.symmetrical_bones['arms']['forearm'][index])
                    eforearm = armature.data.edit_bones[prefix + bone]
                    length = eforearm.length

                    if vatinfo.sbox:
                        eforearm.length = eforearm.length*1.5
                    elif arm.symmetrical_bones['legs'].get('thighlow'):
                        eforearm.length = eforearm.length*1.75
                    else:
                        eforearm.length = eforearm.length*1.25
                    ehand.tail = eforearm.tail
                    eforearm.length = length

        #Extends feet bone if no toe bone is present
        for index, bone in enumerate(arm.symmetrical_bones['legs']['foot']):
            if bone:
                prefix, bone = bone_convert(bone)
                efoot = armature.data.edit_bones[prefix + bone]

                if not arm.symmetrical_bones['legs']['toe0'] or not arm.symmetrical_bones['legs']['toe0'][index]:
                    if efoot.tail.y < 0:
                        efoot.tail.y = efoot.tail.y*5
                    elif efoot.tail.y > 0:
                        efoot.tail.y = efoot.tail.y*-5

                    efoot.tail.z = efoot.tail.z*0.4

        #Extends forearm bone if no hand bone is present
        for index, bone in enumerate(arm.symmetrical_bones['arms']['upperarm']):
            if bone:
                prefix, bone = bone_convert(bone)
                eupperarm = armature.data.edit_bones[prefix + bone]

                if not arm.symmetrical_bones['arms']['hand'] or not arm.symmetrical_bones['arms']['hand'][index]:
                    if arm.symmetrical_bones['arms']['forearm'] and arm.symmetrical_bones['arms']['forearm'][index]:
                        prefix, bone = bone_convert(arm.symmetrical_bones['arms']['forearm'][index])
                        eforearm = armature.data.edit_bones[prefix + bone]

                        length = eupperarm.length
                        eupperarm.length = eupperarm.length*2.5

                        eforearm.tail = eupperarm.tail

                        eupperarm.length = length

        #Extends calf bone if no feet bone is present
        for index, bone in enumerate(arm.symmetrical_bones['legs']['thigh']):
            if bone:
                prefix, bone = bone_convert(bone)
                ethigh = armature.data.edit_bones[prefix + bone]

                if not arm.symmetrical_bones['legs']['foot'] or not arm.symmetrical_bones['legs']['foot'][index]:
                    if arm.symmetrical_bones['legs']['calf'] and arm.symmetrical_bones['legs']['calf'][index]:
                        prefix, bone = bone_convert(arm.symmetrical_bones['legs']['calf'][index])
                        ecalf = armature.data.edit_bones[prefix + bone]

                        length = ethigh.length
                        ethigh.length = ethigh.length*2

                        ecalf.tail = ethigh.tail

                        ethigh.length = length

        if type == 'anim':
            #Fix for legs/arms rotating the wrong way in most characters with the animation armature
            for index, bone in enumerate(arm.symmetrical_bones['arms']['forearm']):
                if bone:
                    prefix, bone = bone_convert(bone)
                    eforearm = armature.data.edit_bones[prefix + bone]

                    if arm.symmetrical_bones['arms']['upperarm'] and arm.symmetrical_bones['arms']['upperarm'][index]:
                        prefix, bone = bone_convert(arm.symmetrical_bones['arms']['forearm'][index])
                        eupperarm = armature.data.edit_bones[prefix + bone]

                        if eforearm.head.y <= eupperarm.head.y:
                            eforearm.head.y = eupperarm.head.y + 0.25*unit

            for index, bone in enumerate(arm.symmetrical_bones['legs']['calf']):
                if bone:
                    prefix, bone = bone_convert(bone)
                    ecalf = armature.data.edit_bones[prefix + bone]

                    if arm.symmetrical_bones['legs']['thigh'] and arm.symmetrical_bones['legs']['thigh'][index]:
                        prefix, bone = bone_convert(arm.symmetrical_bones['legs']['thigh'][index])
                        ethigh = armature.data.edit_bones[prefix + bone]

                        if ecalf.head.y > ethigh.head.y:
                            ecalf.head.y = ethigh.head.y - 0.25*unit
        
        ##Weight armature bone tweaks##
        elif type == 'weight':
            ##Knee/Elbow##
            for index, bone in enumerate(arm.helper_bones['arms']['elbow']):
                if bone:
                    prefix, bone = bone_convert(bone)
                    pelbow = armature.pose.bones[prefix + bone]
                    eelbow = armature.data.edit_bones[prefix + bone]

                    eelbow.tail.xyz = pelbow.head.x, pelbow.head.y + 5*unit, pelbow.head.z

            for index, bone in enumerate(arm.helper_bones['legs']['knee']):
                if bone:
                    prefix, bone = bone_convert(bone)
                    pknee = armature.pose.bones[prefix + bone]
                    eknee = armature.data.edit_bones[prefix + bone]

                    eknee.tail.xyz = pknee.head.x, pknee.head.y - 5*unit, pknee.head.z

            ##Trapezius##
            for index, bone in enumerate(arm.symmetrical_bones['arms']['clavicle']):
                if bone:
                    if arm.helper_bones['arms']['trapezius'] and arm.helper_bones['arms']['trapezius'][index]:
                        prefix, bone = bone_convert(arm.helper_bones['arms']['trapezius'][index])
                        etrapezius = armature.data.edit_bones[prefix + bone]

                        if arm.symmetrical_bones['arms']['upperarm'] and arm.symmetrical_bones['arms']['upperarm'][index]:
                            prefix, bone = bone_convert(arm.symmetrical_bones['arms']['upperarm'][index])
                            pupperarm = armature.pose.bones[prefix + bone]

                            etrapezius.tail = pupperarm.head

            ##Shoulder/Bicep##
            for index, bone in enumerate(arm.symmetrical_bones['arms']['upperarm']):
                if bone:
                    prefix, bone = bone_convert(bone)
                    eupperarm = armature.data.edit_bones[prefix + bone]

                    #Forces upperarm to use shoulder's position if it exists
                    if arm.helper_bones['arms']['shoulder'] and arm.helper_bones['arms']['shoulder'][index]:
                        prefix, bone = bone_convert(arm.helper_bones['arms']['shoulder'][index])
                        pshoulder = armature.pose.bones[prefix + bone]

                        eupperarm.tail = pshoulder.head

                    #Forces upperarm to use bicep's position if they exist
                    elif arm.helper_bones['arms']['bicep'] and arm.helper_bones['arms']['bicep'][index]:
                        prefix, bone = bone_convert(arm.helper_bones['arms']['bicep'][index])
                        pbicep = armature.pose.bones[prefix + bone]

                        eupperarm.tail = pbicep.head

                    #If shoulder and bicep are present
                    if arm.helper_bones['arms']['shoulder'] and arm.helper_bones['arms']['bicep'] and arm.helper_bones['arms']['shoulder'][index] and arm.helper_bones['arms']['bicep'][index]:
                        prefix, bone = bone_convert(arm.helper_bones['arms']['shoulder'][index])
                        eshoulder = armature.data.edit_bones[prefix + bone]

                        prefix, bone = bone_convert(arm.helper_bones['arms']['bicep'][index])
                        pbicep = armature.pose.bones[prefix + bone]
                        ebicep = armature.data.edit_bones[prefix + bone]

                        eshoulder.head = eupperarm.head
                        eupperarm.head = eshoulder.tail
                        eupperarm.tail = pbicep.head

                        if arm.symmetrical_bones['arms']['forearm'] and arm.symmetrical_bones['arms']['forearm'][index]:
                            prefix, bone = bone_convert(arm.symmetrical_bones['arms']['forearm'][index])
                            pforearm = armature.pose.bones[prefix + bone]
                            ebicep.tail = pforearm.head

                    #Else if only shoulder is present
                    elif arm.helper_bones['arms']['shoulder'] and arm.helper_bones['arms']['shoulder'][index]:
                        prefix, bone = bone_convert(arm.helper_bones['arms']['shoulder'][index])
                        eshoulder = armature.data.edit_bones[prefix + bone]

                        eshoulder.head = eupperarm.head
                        eupperarm.head = eshoulder.tail

                        if arm.symmetrical_bones['arms']['forearm'] and arm.symmetrical_bones['arms']['forearm'][index]:
                            prefix, bone = bone_convert(arm.symmetrical_bones['arms']['forearm'][index])
                            pforearm = armature.pose.bones[prefix + bone]

                            eupperarm.tail = pforearm.head

                    #Else if only bicep is present
                    elif arm.helper_bones['arms']['bicep'] and arm.helper_bones['arms']['bicep'][index]:
                        prefix, bone = bone_convert(arm.helper_bones['arms']['bicep'][index])
                        pbicep = armature.pose.bones[prefix + bone]
                        ebicep = armature.data.edit_bones[prefix + bone]

                        eupperarm.tail = pbicep.head

                        if arm.symmetrical_bones['arms']['forearm'] and arm.symmetrical_bones['arms']['forearm'][index]:
                            prefix, bone = bone_convert(arm.symmetrical_bones['arms']['forearm'][index])
                            pforearm = armature.pose.bones[prefix + bone]
                            ebicep.tail = pforearm.head

            ##Ulna/Wrist##
            for index, bone in enumerate(arm.symmetrical_bones['arms']['forearm']):
                if bone:
                    prefix, bone = bone_convert(bone)
                    eforearm = armature.data.edit_bones[prefix + bone]

                    #Force forearm to use forearm_driven's position if available
                    if arm.helper_bones['viewmodel']['forearm_driven'] and arm.helper_bones['viewmodel']['forearm_driven'][index]:
                        prefix, bone = bone_convert(arm.helper_bones['viewmodel']['forearm_driven'][index])
                        pforearm_driven = armature.pose.bones[prefix + bone]

                        eforearm.tail = pforearm_driven.head
                    else:
                        if arm.helper_bones['arms']['ulna'] and arm.helper_bones['arms']['ulna'][index]:
                            prefix, bone = bone_convert(arm.helper_bones['arms']['ulna'][index])
                            pulna = armature.pose.bones[prefix + bone]
                            
                            eforearm.tail = pulna.head

                    if arm.symmetrical_bones['arms']['hand'] and arm.symmetrical_bones['arms']['hand'][index]:
                        prefix, bone = bone_convert(arm.symmetrical_bones['arms']['hand'][index])
                        phand = armature.pose.bones[prefix + bone]
                        ehand = armature.data.edit_bones[prefix + bone]

                        if arm.helper_bones['arms']['ulna'] and arm.helper_bones['viewmodel']['forearm_driven'] and arm.helper_bones['arms']['ulna'][index] and arm.helper_bones['viewmodel']['forearm_driven'][index]:
                            prefix, bone = bone_convert(arm.helper_bones['arms']['ulna'][index])
                            eulna = armature.data.edit_bones[prefix + bone]

                            eulna.tail = phand.head

                            prefix, bone = bone_convert(arm.helper_bones['viewmodel']['forearm_driven'][index])
                            eforearm_driven = armature.data.edit_bones[prefix + bone]

                            eforearm_driven.tail = eulna.head

                        #If both ulna and wrist are present
                        elif arm.helper_bones['arms']['ulna'] and arm.helper_bones['arms']['wrist'] and arm.helper_bones['arms']['ulna'][index] and arm.helper_bones['arms']['wrist'][index]:
                            prefix, bone = bone_convert(arm.helper_bones['arms']['ulna'][index])
                            eulna = armature.data.edit_bones[prefix + bone]

                            eulna.tail = phand.head
                            eulna.length = eulna.length/1.6

                            prefix, bone = bone_convert(arm.helper_bones['arms']['wrist'][index])
                            ewrist = armature.data.edit_bones[prefix + bone]

                            ewrist.head = eulna.tail
                            ewrist.tail = phand.head

                        #Else if only ulna is present
                        elif arm.helper_bones['arms']['ulna'] and arm.helper_bones['arms']['ulna'][index]:
                            prefix, bone = bone_convert(arm.helper_bones['arms']['ulna'][index])
                            eulna = armature.data.edit_bones[prefix + bone]

                            eulna.tail = phand.head

                        #Else if only wrist is present
                        elif arm.helper_bones['arms']['wrist'] and arm.helper_bones['arms']['wrist'][index]:
                            prefix, bone = bone_convert(arm.helper_bones['arms']['wrist'][index])
                            ewrist = armature.data.edit_bones[prefix + bone]

                            eforearm.length = eforearm.length/1.3

                            ewrist.head = eforearm.tail
                            ewrist.tail = phand.head

                            eforearm.tail = ewrist.head
                            ewrist.use_connect = True

                        else: #If neither are present
                            eforearm.tail = phand.head
                            ehand.use_connect = True

            ##Quadricep##
            for index, bone in enumerate(arm.symmetrical_bones['legs']['thigh']):
                if bone:
                    prefix, bone = bone_convert(bone)
                    ethigh = armature.data.edit_bones[prefix + bone]
                    #bone2 present to avoid problems with the last condition

                    #Force thigh to use quad's position if available
                    if arm.helper_bones['legs']['quadricep'] and arm.helper_bones['legs']['quadricep'][index]:
                        prefix2, bone2 = bone_convert(arm.helper_bones['legs']['quadricep'][index])
                        pquadricep = armature.pose.bones[prefix2 + bone2]
                        equadricep = armature.data.edit_bones[prefix2 + bone2]

                        ethigh.tail = pquadricep.head

                        if arm.symmetrical_bones['legs']['calf'] and arm.symmetrical_bones['legs']['calf'][index]:
                            prefix2, bone2 = bone_convert(arm.symmetrical_bones['legs']['calf'][index])
                            pcalf = armature.pose.bones[prefix2 + bone2]
                            equadricep.tail = pcalf.head

                    #Gluteus (Only for Zoey)
                    if arm.helper_bones['others'].get('gluteus'):
                        if arm.helper_bones['others']['gluteus'] and arm.helper_bones['others']['gluteus'][index]:
                            prefix2, bone2 = bone_convert(arm.helper_bones['others']['gluteus'][index])
                            pgluteus = armature.pose.bones[prefix2 + bone2]

                            pgluteus.rotation_quaternion[3] = -1
                            pgluteus.scale.xyz = 25,25,25

                            bpy.ops.object.mode_set(mode='POSE')
                            armature.data.bones[prefix2 + bone2].select = True
                            bpy.ops.pose.armature_apply(selected=True)
                            bpy.ops.pose.select_all(action='DESELECT')
                            bpy.ops.object.mode_set(mode='EDIT')

                            ethigh = armature.data.edit_bones[prefix + bone]
                            egluteus = armature.data.edit_bones[prefix2 + bone2]

                            ethigh.head = egluteus.tail

                    #Shoulder1 (Only for Louis)
                    if arm.helper_bones['arms'].get('shoulder1'):
                        if arm.symmetrical_bones['arms']['clavicle']:
                            prefix, bone = bone_convert(arm.symmetrical_bones['arms']['clavicle'][0])
                            eclavicle = armature.data.edit_bones[prefix + bone]

                            if arm.helper_bones['arms']['shoulder']:
                                prefix, bone = bone_convert(arm.helper_bones['arms']['shoulder'][0])
                                
                                eshoulder = armature.data.edit_bones[prefix + bone]

                                eclavicle.tail = eshoulder.head

                            elif arm.symmetrical_bones['arms']['upperarm']:
                                prefix, bone = bone_convert(arm.symmetrical_bones['arms']['upperarm'][0])
                                eupperarm = armature.data.edit_bones[prefix + bone]

                                eclavicle.tail = eupperarm.head

            ##Thumbroot## (Only for viewmodels)
            for index, bone in enumerate(arm.symmetrical_bones['arms']['hand']):
                if bone:
                    prefix, bone = bone_convert(bone)
                    phand = armature.pose.bones[prefix + bone]
                    ehand = armature.data.edit_bones[prefix + bone]

                    if arm.helper_bones['viewmodel']['thumbroot'] and arm.helper_bones['viewmodel']['thumbroot'][index]:
                        prefix, bone = bone_convert(arm.helper_bones['viewmodel']['thumbroot'][index])
                        ethumbroot = armature.data.edit_bones[prefix + bone]

                        ethumbroot.head = phand.head

                        if arm.symmetrical_bones['fingers']['finger0'] and arm.symmetrical_bones['fingers']['finger0'][index]:
                            prefix, bone = bone_convert(arm.symmetrical_bones['fingers']['finger0'][index])
                            pfinger0 = armature.pose.bones[prefix + bone]

                            ethumbroot.tail = pfinger0.head

            if vatinfo.sbox:
                for index, bone in enumerate(arm.symmetrical_bones['legs']['thigh']):
                    if bone:
                        prefix, bone = bone_convert(bone)
                        ethigh = armature.data.edit_bones[prefix + bone]

                        if arm.helper_bones['legs']['quadricep'] and arm.helper_bones['legs']['quadricep'][index]:
                            prefix, bone = bone_convert(arm.helper_bones['legs']['quadricep'][index])
                            equadricep = armature.data.edit_bones[prefix + bone]

                            equadricep.head = ethigh.head
                            equadricep.length = equadricep.length / 3
                            
                            ethigh.head = equadricep.tail
                            
                            if arm.symmetrical_bones['legs']['calf'] and arm.symmetrical_bones['legs']['calf'][index]:
                                prefix, bone = bone_convert(arm.symmetrical_bones['legs']['calf'][index])
                                ecalf = armature.data.edit_bones[prefix + bone]

                                ethigh.tail = ecalf.head

                for index, bone in enumerate(arm.symmetrical_bones['legs']['foot']):
                    if bone:
                        prefix, bone = bone_convert(bone)
                        efoot = armature.data.edit_bones[prefix + bone]

                        if arm.helper_bones['legs'].get('lowerleg') and arm.helper_bones['legs']['lowerleg'][index]:
                            prefix, bone = bone_convert(arm.helper_bones['legs']['lowerleg'][index])
                            elowerleg = armature.data.edit_bones[prefix + bone]

                            elowerleg.tail = efoot.head

                for index, bone in enumerate(arm.symmetrical_bones['arms']['hand']):
                    if bone:
                        prefix, bone = bone_convert(bone)
                        ehand = armature.data.edit_bones[prefix + bone]

                        if arm.helper_bones['arms']['wrist'] and arm.helper_bones['arms']['wrist'][index]:
                            prefix, bone = bone_convert(arm.helper_bones['arms']['wrist'][index])
                            ewrist = armature.data.edit_bones[prefix + bone]

                            ewrist.length = ewrist.length*1.35
                            ehand.tail = ewrist.tail
                            ewrist.length = ewrist.length/1.5
                            ehand.head = ewrist.tail

        if vatinfo.titanfall:
            #Changes pelvis position to avoid deletion
            if arm.central_bones['pelvis'] and arm.central_bones['spine1']:
                prefix, bone = bone_convert(arm.central_bones['pelvis'][0])
                epelvis = armature.data.edit_bones[prefix + bone]
                prefix, bone = bone_convert(arm.central_bones['spine1'][0])
                espine1 = armature.data.edit_bones[prefix + bone]

                epelvis.tail = espine1.head
                epelvis.length = epelvis.length/3

            #Aligns calf to the thigh
            for index, bone in enumerate(arm.symmetrical_bones['legs']['calf']):
                if bone:
                    prefix, bone = bone_convert(bone)
                    ecalf = armature.data.edit_bones[prefix + bone]

                    if arm.symmetrical_bones['legs'].get('thighlow') and arm.symmetrical_bones['legs']['thighlow'][index]:
                        prefix, bone = bone_convert(arm.symmetrical_bones['legs']['thighlow'][index])
                        ethighlow = armature.data.edit_bones[prefix + bone]

                        ecalf.head = ethighlow.tail
                        ecalf.use_connect = True

                    elif arm.symmetrical_bones['legs']['thigh'] and arm.symmetrical_bones['legs']['thigh'][index]:
                        prefix, bone = bone_convert(arm.symmetrical_bones['legs']['thigh'][index])
                        ethigh = armature.data.edit_bones[prefix + bone]

                        ecalf.head = ethigh.tail

            #Removes head bone since it serves no purpose and neck2 serves its purpose anyways, and repositions both neck bones to be more accurate to where they would really be
            if arm.central_bones['head'] and arm.central_bones['neck'] and arm.central_bones.get('neck2'):
                prefix, bone = bone_convert(arm.central_bones['head'][0])
                ehead = armature.data.edit_bones[prefix + bone]
                prefix, bone = bone_convert(arm.central_bones['neck'][0])
                eneck = armature.data.edit_bones[prefix + bone]
                prefix, bone = bone_convert(arm.central_bones['neck2'][0])
                eneck2 = armature.data.edit_bones[prefix + bone]

                eneck.tail = eneck2.head
                eneck2.tail = ehead.tail

                eneck2.parent = eneck

                eneck2.use_connect = True

                armature.data.edit_bones.remove(ehead)
    
        #Corrects central bones roll values to 0
        if type == 'anim':
            for container, bone in arm.central_bones.items():
                for bone in bone:
                    if bone:
                        if vatinfo.titanfall and bone.title().count('Head'):
                            continue
                        prefix, bone = bone_convert(bone)
                        ebone = armature.data.edit_bones[prefix + bone]

                        ebone.roll = 0

        #Finger tips tweak
        for container, bone in arm.symmetrical_bones['fingers'].items():
            if container == 'finger0' or container == 'finger1' or container == 'finger2' or container == 'finger3' or container == 'finger4':
                for index, bone in enumerate(bone):
                    if bone:
                        prefix, bone = bone_convert(bone)
                        tip = container[0:7] + '2'
                        middle = container[0:7] + '1'

                        if arm.symmetrical_bones['fingers'][tip] and arm.symmetrical_bones['fingers'][tip][index]:
                            prefix, bone = bone_convert(arm.symmetrical_bones['fingers'][middle][index])
                            ebone = armature.data.edit_bones[prefix + bone]
                            length = ebone.length
                            
                            ebone.length = length*2

                            prefix, bone = bone_convert(arm.symmetrical_bones['fingers'][tip][index])
                            armature.data.edit_bones[prefix + bone].tail.xyz = ebone.tail.x, ebone.tail.y, ebone.tail.z

                            ebone.length = length

                        elif arm.symmetrical_bones['fingers'][middle] and arm.symmetrical_bones['fingers'][middle][index]:
                            prefix, bone = bone_convert(arm.symmetrical_bones['fingers'][container][index])
                            ebone = armature.data.edit_bones[prefix + bone]
                            length = ebone.length
                            
                            ebone.length = length*2

                            prefix, bone = bone_convert(arm.symmetrical_bones['fingers'][middle][index])
                            armature.data.edit_bones[prefix + bone].tail = ebone.tail

                            ebone.length = length
        
        #If no head
        if not arm.central_bones['head']:
            ebone = None
            ebone2 = None

            if arm.central_bones['spine4'] and arm.central_bones['spine2']:
                prefix, bone = bone_convert(arm.central_bones['spine2'][0])
                ebone = armature.data.edit_bones[prefix + bone]
                prefix, bone = bone_convert(arm.central_bones['spine4'][0])
                ebone2 = armature.data.edit_bones[prefix + bone]

            elif arm.central_bones['spine3'] and arm.central_bones['neck']:
                prefix, bone = bone_convert(arm.central_bones['spine3'][0])
                ebone = armature.data.edit_bones[prefix + bone]
                prefix, bone = bone_convert(arm.central_bones['neck'][0])
                ebone2 = armature.data.edit_bones[prefix + bone]

            elif arm.central_bones['spine3'] and arm.central_bones['spine2']:
                prefix, bone = bone_convert(arm.central_bones['spine2'][0])
                ebone = armature.data.edit_bones[prefix + bone]
                prefix, bone = bone_convert(arm.central_bones['spine3'][0])
                ebone2 = armature.data.edit_bones[prefix + bone]

            if ebone and ebone2:
                length = ebone.length
                ebone.length = ebone.length*1.75

                ebone2.tail = ebone.tail

                ebone.length = length

                ebone2.tail.y = ebone2.head.y
            else:
                #Gmod default viewmodels only have spine4, this aligns it
                if arm.central_bones['spine4']:
                    prefix, bone = bone_convert(arm.central_bones['spine4'][0])
                    ebone = armature.data.edit_bones[prefix + bone]

                    ebone.tail.x = ebone.head.x

        #Rotates bones with no children to be more readable while keeping their isolated form intact
        if arm.chainless_bones:
            for bone in arm.chainless_bones:
                prefix, bone = bone_convert(bone)
                ebone = armature.data.edit_bones[prefix + bone]

                if type == 'anim':
                    if ebone.children[0].name.endswith('.isolated'):
                        ebone2 = armature.data.edit_bones[ebone.children[0].name]
                        ebone2.parent = None
                
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.armature_apply()
            bpy.ops.pose.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='EDIT')
            
            if type == 'anim':
                for bone in arm.chainless_bones:
                    prefix, bone = bone_convert(bone)
                    ebone = armature.data.edit_bones[prefix + bone]
                    ebone2 = armature.data.edit_bones[prefix + bone + '.isolated']
                    ebone2.parent = ebone

        armature.location = arm.armature.location
        armature.rotation_euler = arm.armature.rotation_euler
        armature.scale = arm.armature.scale

        #Final touches to the armature
        armature.data.display_type = 'OCTAHEDRAL'
        armature.show_in_front = True

        if type == 'weight':
            armature.data.show_bone_custom_shapes = False
        elif type == 'anim':
            armature.data.rigify_advanced_generation = True
            armature.data.rigify_generate_mode = 'new'
            armature.data.rigify_rig_basename = arm.armature.name + '.anim'
            
        bpy.ops.object.mode_set(mode='OBJECT')

    #Deletion
    elif action == 1 or action == 2:

        #Checks if they weren't deleted already
        if type == 'weight':
            try:
                bpy.data.objects.remove(arm.weight_armature)
            except:
                print("Weight armature already deleted, cleaning rest")
            try:
                bpy.data.armatures.remove(arm.weight_armature_real)
            except:
                pass
                    
            vatinfo.weight_armature = False
            arm.weight_armature = None
            arm.weight_armature_real = None
            
        elif type == 'anim':
            if not vatinfo.animation_armature_setup:
                try:
                    animation_data = bpy.data.objects[arm.animation_armature_real['target_object']].data
                    bpy.data.objects[arm.animation_armature_real['target_object']].data = bpy.data.meshes[arm.animation_armature_real['target_object_data']]
                    bpy.data.meshes.remove(animation_data)
                except:
                    pass

            try:
                bpy.data.objects.remove(arm.animation_armature)
            except:
                print("Animation armature already deleted, cleaning rest")

            bpy.data.armatures.remove(arm.animation_armature_real)

            if action == 1 and vatinfo.animation_armature_setup:
                try:
                    object = bpy.data.objects[arm.armature.name + '.anim']
                    bpy.data.objects.remove(object)
                except:
                    pass

                try:
                    armature = bpy.data.armatures[arm.armature_real.name + '.anim']
                    bpy.data.armatures.remove(armature)
                except:
                    pass
            elif action == 2:
                arm.animation_armature = bpy.data.objects[arm.armature.name + '.anim']
                arm.animation_armature_real = bpy.data.armatures[arm.armature_real.name + '.anim']
            
            #Checks if retarget empties are present, if so, remove them
            if action == 1:
                armature = arm.armature

                #Removes viewmodel camera if present
                try:
                    camera = bpy.data.objects['viewmodel_camera']
                    camera_data = bpy.data.cameras['viewmodel_camera']
                    bpy.data.objects.remove(camera)
                    bpy.data.cameras.remove(camera_data)
                except:
                    pass
                    
                #Removes original armature constraints
                for cat in arm.symmetrical_bones.keys():
                    for bone in arm.symmetrical_bones[cat].values():
                        for bone in bone:
                            if bone:
                                prefix, bone = bone_convert(bone)
                                try:
                                    constraint = armature.pose.bones[prefix + bone].constraints["Retarget Location"]
                                    armature.pose.bones[prefix + bone].constraints.remove(constraint)
                                except:
                                    pass
                            
                                try:
                                    constraint = armature.pose.bones[prefix + bone].constraints["Retarget Rotation"]
                                    armature.pose.bones[prefix + bone].constraints.remove(constraint)
                                except:
                                    pass
                                
                for container, bone in arm.central_bones.items():
                    for bone in bone:
                        if bone:
                            try:
                                constraint = armature.pose.bones[prefix + bone].constraints["Retarget Location"]
                                armature.pose.bones[prefix + bone].constraints.remove(constraint)
                            except:
                                pass

                            try:
                                constraint = armature.pose.bones[prefix + bone].constraints["Retarget Rotation"]
                                armature.pose.bones[prefix + bone].constraints.remove(constraint)
                            except:
                                pass

                for cat in arm.helper_bones.keys():
                    for container, bone in arm.helper_bones[cat].items():
                        if container == 'elbow' or container == 'knee':
                            for bone in bone:
                                if bone:
                                    prefix2, bone2 = bone_convert(bone)

                                    try:
                                        constraint = armature.pose.bones[prefix2 + bone2].constraints["Retarget Location"]
                                        armature.pose.bones[prefix2 + bone2].constraints.remove(constraint)
                                    except:
                                        pass

                                    try:
                                        constraint = armature.pose.bones[prefix2 + bone2].constraints["Retarget Rotation"]
                                        armature.pose.bones[prefix2 + bone2].constraints.remove(constraint)
                                    except:
                                        pass

                for container, bone in arm.other_bones.items():
                    if container == 'weapon' or container == 'viewmodel':
                        for bone in bone:
                            if bone:
                                prefix, bone = bone_convert(bone)
                                try:
                                    constraint = armature.pose.bones[prefix + bone].constraints["Retarget Location"]
                                    armature.pose.bones[prefix + bone].constraints.remove(constraint)
                                except:
                                    pass

                                try:
                                    constraint = armature.pose.bones[prefix + bone].constraints["Retarget Rotation"]
                                    armature.pose.bones[prefix + bone].constraints.remove(constraint)
                                except:
                                    pass

                for container, bone in arm.custom_bones.items():
                    for bone in bone:
                        if bone:
                            try:
                                constraint = armature.pose.bones[bone].constraints["Retarget Location"]
                                armature.pose.bones[bone].constraints.remove(constraint)
                            except:
                                pass

                            try:
                                constraint = armature.pose.bones[bone].constraints["Retarget Rotation"]
                                armature.pose.bones[bone].constraints.remove(constraint)
                            except:
                                pass

                try:
                    collection = bpy.data.collections["Retarget Empties ({})".format(arm.armature.name)[0:60]]

                    if collection.objects.values():
                        for object in collection.objects.values():
                            data = object.data
                            bpy.data.objects.remove(object)

                    bpy.data.collections.remove(collection)
                except:
                    pass

                arm.animation_armature = None
                arm.animation_armature_real = None
                vatinfo.animation_armature = False
            
        #Reselects original armature for the sake of convenience
        armature = arm.armature

        if type == 'anim':
            if armature.hide_get() == True:
                armature.hide_set(False)

        if armature.visible_get():
            armature.select_set(True)
            bpy.context.view_layer.objects.active = armature

#Thanku Orin for the enhanced code snippet
def bone_convert(bone):
    vatinfo = bpy.context.scene.vatinfo
    prefix = ''

    # 'h' = Helper
    # 'a' = Attachments
    # 'p' = Standard

    bone = bone.split('.')
    if len(bone) > 1:
        if bone[0] == 'h1':
            prefix = Prefixes.helper
        elif bone[0] == 'h2':
            prefix = Prefixes.helper2
        elif bone[0] == 'a1':
            prefix = Prefixes.attachment
        elif bone[0] == 'a2':
            prefix = Prefixes.attachment2
        elif bone[0] == 'p1':
            prefix = vatinfo.prefix
        elif bone[0] == 'p2':
            prefix = Prefixes.other

        bone = bone[1]
    else:
        bone = bone[0]

    return prefix, bone

def generate_shapekey_dict(dictionary, raw_list):
    for shapekey in raw_list:
        #Basis
        if shapekey.casefold().count('basis') or shapekey.casefold().count('base'):
            dictionary['basis']['basis'] = shapekey

        #Eyebrows
        if shapekey.upper().count('AU1AU2L') or shapekey.upper().count('AU1AU2R'):
            dictionary['eyebrows']['AU1AU2'] = shapekey
        elif shapekey.upper().count('AU1AU4L') or shapekey.upper().count('AU1AU4R'):
            dictionary['eyebrows']['AU1AU4'] = shapekey
        elif shapekey.upper().count('AU2AU4L') or shapekey.upper().count('AU2AU4R'):
            dictionary['eyebrows']['AU2AU4'] = shapekey
        elif shapekey.upper().count('AU1L') or shapekey.upper().count('AU1R'):
            dictionary['eyebrows']['AU1'] = shapekey
        elif shapekey.upper().count('AU2L') or shapekey.upper().count('AU2R'):
            dictionary['eyebrows']['AU2'] = shapekey
        elif shapekey.upper().count('AU4L') or shapekey.upper().count('AU4R'):
            dictionary['eyebrows']['AU4'] = shapekey

        #Eyes
        elif shapekey.lower().count('f01') or shapekey.lower().count('frame1'):
            dictionary['eyes']['f01'] = shapekey
        elif shapekey.lower().count('f02') or shapekey.lower().count('frame2'):
            dictionary['eyes']['f02'] = shapekey
        elif shapekey.lower().count('f03') or shapekey.lower().count('frame3'):
            dictionary['eyes']['f03'] = shapekey
        elif shapekey.lower().count('f04'):
            dictionary['eyes']['f04'] = shapekey
        elif shapekey.upper().count('AU42'):
            dictionary['eyes']['AU42'] = shapekey
        
        #Cheek
        elif shapekey.upper().count('AU6ZL') or shapekey.upper().count('AU6ZR'):
            dictionary['cheek']['AU6Z'] = shapekey
        elif shapekey.upper().count('AU13L') or shapekey.upper().count('AU13R'):
            dictionary['cheek']['AU13'] = shapekey

        #Nose
        elif shapekey.upper().count('AU9L') or shapekey.upper().count('AU9R'):
            dictionary['nose']['AU9'] = shapekey
        elif shapekey.upper().count('AU38'):
            dictionary['nose']['AU38'] = shapekey

        #Mouth
        elif shapekey.upper().count('AU12L') or shapekey.upper().count('AU12R'):
            dictionary['mouth']['AU12'] = shapekey
        elif shapekey.upper().count('AU15L') or shapekey.upper().count('AU15R'):
            dictionary['mouth']['AU15'] = shapekey
        elif shapekey.upper().count('AU10L') or shapekey.upper().count('AU10R'):
            dictionary['mouth']['AU10'] = shapekey
        elif shapekey.upper().count('AU17DL') or shapekey.upper().count('AU17DR'):
            dictionary['mouth']['AU17D'] = shapekey
        elif shapekey.upper().count('AU16L') or shapekey.upper().count('AU16R'):
            dictionary['mouth']['AU16'] = shapekey
        elif shapekey.upper().count('AU32'):
            dictionary['mouth']['AU32'] = shapekey
        elif shapekey.upper().count('AU24'):
            dictionary['mouth']['AU24'] = shapekey
        elif shapekey.upper().count('AU18ZL') or shapekey.upper().count('AU18ZR'):
            dictionary['mouth']['AU18Z'] = shapekey
        elif shapekey.upper().count('AU22ZL') or shapekey.upper().count('AU22ZR'):
            dictionary['mouth']['AU22Z'] = shapekey
        elif shapekey.upper().count('AD96L'):
            dictionary['mouth']['AD96L'] = shapekey
        elif shapekey.upper().count('AD96R'):
            dictionary['mouth']['AD96R'] = shapekey

        #Chin
        elif shapekey.upper().count('AU31'):
            dictionary['chin']['AU31'] = shapekey
        elif shapekey.upper().count('AU26L') or shapekey.upper().count('AU26R'):
            dictionary['chin']['AU26'] = shapekey
        elif shapekey.upper().count('AU27L') or shapekey.upper().count('AU27R'):
            dictionary['chin']['AU27'] = shapekey
        elif shapekey.upper().count('AU27ZL') or shapekey.upper().count('AU27ZR'):
            dictionary['chin']['AU27Z'] = shapekey
        elif shapekey.upper().count('AD30L'):
            dictionary['chin']['AD30L'] = shapekey
        elif shapekey.upper().count('AD30R'):
            dictionary['chin']['AD30R'] = shapekey
        elif shapekey.upper().count('AU17L') or shapekey.upper().count('AU17R'):
            dictionary['chin']['AU17'] = shapekey

    return dictionary

def update_armature(self, context):
    armature(1)