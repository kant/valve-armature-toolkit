import bpy

class Prefixes: #Self explanatory

    current = ""

    #Prefix variables for reference
    default = "ValveBiped.Bip01_"
    sfm = "bip_"
    helper = "hlp_"
    other = "ValveBiped."

class BoneList: #Lists of bones used for other operations

    #List of bones that will be filled with the armature's
    symmetrical_bones = [] #L/R
    central_bones = [] #Head, spine...
    helper_bones = [] #Knee, wrist...
    other_bones = [] #Jacket, attachments...
    custom_bones = [] #User made bones with no, or other prefix

    def getbones():
        vatproperties = bpy.context.scene.vatproperties
        armature = bpy.data.objects[vatproperties.target_armature.name]

        #Cleans bone list
        BoneList.symmetrical_bones = []
        BoneList.central_bones = []
        BoneList.helper_bones = []
        BoneList.other_bones = []
        BoneList.custom_bones = []

        full_bonelist = armature.data.bones.keys() #Gets all bones available in the armature

        #Checks wether or not they're central, symmetrical, helper, other, or custom bones, then removes their prefix/suffix and adds them into a group
        for bone in full_bonelist:

            if vatproperties.custom_scheme_enabled == True and vatproperties.custom_scheme_prefix != "":
                if bone.startswith(custom_scheme_prefix + bone.count("L_") == 0 or bone.count("R_") == 0 or bone.count("_L") == 0 or bone.count("_R") == 0):
                    vatproperties.scheme = 3
                    BoneList.symmetrical_bones.append(bone.replace(custom_scheme_prefix, ""))
                elif bone.startswith(custom_scheme_prefix):
                    BoneList.central_bones.append(bone.replace(custom_scheme_prefix, ""))

            #Source and Blender prefixes
            if bone.startswith("ValveBiped."):
                vatproperties.sfm_armature = False
                Prefixes.current = "ValveBiped.Bip01_"

                if bone.startswith("ValveBiped.Bip01_L_") or bone.startswith("ValveBiped.Bip01_R_"): #Symmetrical
                    vatproperties.scheme = 0
                    BoneList.symmetrical_bones.append(bone.replace("ValveBiped.Bip01_", ""))

                elif bone.endswith("_L") or bone.endswith("_R"):
                    vatproperties.scheme = 1
                    BoneList.symmetrical_bones.append(bone.replace("ValveBiped.Bip01_", ""))

                elif bone.startswith("ValveBiped.Bip01_"): #Central
                    BoneList.central_bones.append(bone.replace("ValveBiped.Bip01_", ""))
                    
                else: #Other
                    BoneList.other_bones.append(bone.replace("ValveBiped.", ""))

            #SFM prefix
            elif bone.startswith("bip_"): # Central
                vatproperties.sfm_armature = True
                vatproperties.scheme = 2
                Prefixes.current = "bip_"

                if bone.endswith("_L") or bone.endswith("_R"): #Symmetrical
                    BoneList.symmetrical_bones.append(bone.replace("bip_", ""))

                else:
                    BoneList.central_bones.append(bone.replace("bip_", ""))

            #Helper prefix
            elif bone.startswith("hlp_"): #Helper
                BoneList.helper_bones.append(bone.replace("hlp_", ""))
            #No/Different prefix
            else:
                BoneList.custom_bones.append(bone)

        if BoneList.symmetrical_bones == [] and BoneList.central_bones == [] and BoneList.other_bones == []:
            #Unknown armature
            vatproperties.scheme = -1

        print(BoneList.symmetrical_bones)
        print(BoneList.central_bones)
        print(BoneList.helper_bones)
        print(BoneList.other_bones)
        print(BoneList.custom_bones)

class SchemeType: #Scheme type that's currently being used by the armature

    def getscheme(bone):
        vatproperties = bpy.context.scene.vatproperties
        armature = bpy.data.objects[vatproperties.target_armature.name]

        #If not an SFM armature, check if the armature has the Source or Blender armature
        if vatproperties.sfm_armature == False:
            bone = Prefixes.current + bone
            if bone.startswith("ValveBiped.Bip01_L_") or bone.startswith("ValveBiped.Bip01_R_"):
                vatproperties.scheme = 0
            elif bone.endswith("_L") or bone.endswith("_R"):
                vatproperties.scheme = 1

    def execute(self, context):
        vatproperties = bpy.context.scene.vatproperties

        if vatproperties.target_armature != None:
            BoneList.getbones()
            for bone in BoneList.symmetrical_bones:
                SchemeType.getscheme(bone)
                
            if vatproperties.sfm_armature == False:
                if vatproperties.scheme == 0:
                    print("Current Scheme: Source")
                elif vatproperties.scheme == 1:
                    print("Current Scheme: Blender")
            if vatproperties.sfm_armature == True:
                print("Current Scheme: Source (SFM)")

class ArmatureRename: #Scheme changer
    
    def rename(bone, scheme, helper): #Which bone, to which scheme and if it's a helper bone
        vatproperties = bpy.context.scene.vatproperties
        armature = bpy.data.armatures[vatproperties.target_armature.data.name]

        #Current or helper prefix
        if helper == 1:
            prefix = Prefixes.helper
        else:
            prefix = Prefixes.current

        #To which scheme
        if scheme == 1: #Source -> Blender
            if bone.startswith("L_"):
                armature.bones[prefix + bone].name = prefix + bone.replace("L_", "") + "_L"
            elif bone.startswith("R_"):
                armature.bones[prefix + bone].name = prefix + bone.replace("R_", "") + "_R"
            vatproperties.scheme = 1
        elif scheme == 0: #Blender -> Source
            if bone.endswith("_L"):
                armature.bones[prefix + bone].name = prefix + "L_" + bone.replace("_L", "")
            elif bone.endswith("_R"):
                armature.bones[prefix + bone].name = prefix + "R_" + bone.replace("_R", "")
            vatproperties.scheme = 0
                
    def execute(scheme):
        for bone in BoneList.symmetrical_bones:
                ArmatureRename.rename(bone, scheme, 0)
            
        if BoneList.helper_bones != []:
            for bone in BoneList.helper_bones:
                ArmatureRename.rename(bone, scheme, 1)

        BoneList.getbones() #Refreshes bone list
            
class ConstraintSymmetry: #Adds loc/rot constraints to the armature

    #Constraint checks
    loc = ""
    rot = ""

    #Variables for end report
    op = 0
    loc_bonelist = []
    rot_bonelist = []

    def getconstraint(bone):
        vatproperties = bpy.context.scene.vatproperties
        armature = bpy.data.objects[vatproperties.target_armature.name]
        prefix = Prefixes.current

        try:
            ConstraintSymmetry.loc = armature.pose.bones[prefix + bone].constraints['Constraint Symmetry Location']
        except:
            ConstraintSymmetry.loc = ""
        try:
            ConstraintSymmetry.rot = armature.pose.bones[prefix + bone].constraints['Constraint Symmetry Rotation']
        except:
            ConstraintSymmetry.rot = ""

    def constraint(bone, side, action, helper): #Creates or deletes constraints based on action
        vatproperties = bpy.context.scene.vatproperties
        armature = bpy.data.objects[vatproperties.target_armature.name]

        #Cleans bone list
        ConstraintSymmetry.loc_bonelist = []
        ConstraintSymmetry.rot_bonelist = []

        ConstraintSymmetry.getconstraint(bone) #Checks for already existing constraints

        if helper == 1:
            prefix = Prefixes.helper
        else:
            prefix = Prefixes.current

        #Creation
        if action == 0:
            ConstraintSymmetry.op = 0

            #Left side
            if vatproperties.affected_side == 'OP1':

                #Location
                if ConstraintSymmetry.loc == "":
                    if bone.startswith("L_") or bone.endswith("_L"):
                        loc = armature.pose.bones[prefix + bone].constraints.new('COPY_LOCATION')

                        #Constraint parameters
                        loc.name = "Constraint Symmetry Location"
                        loc.target = armature
                        loc.invert_x = True
                        if bone.startswith("L_"):
                            loc.subtarget = prefix + "R_" + bone.replace("L_", "")
                        elif bone.endswith("_L"):
                            loc.subtarget = prefix + bone.replace("_L", "") + "_R"
                else:
                    ConstraintSymmetry.loc_bonelist.append(bone)

                #Rotation
                if ConstraintSymmetry.rot == "":
                    if bone.startswith("L_") or bone.endswith("_L"):
                        rot = armature.pose.bones[prefix + bone].constraints.new('COPY_ROTATION')

                        #Constraint parameters
                        rot.name = "Constraint Symmetry Rotation"
                        rot.target = armature
                        rot.target_space = 'LOCAL'
                        rot.owner_space = 'LOCAL'
                        rot.invert_y = True
                        rot.invert_x = True
                        if bone.startswith("L_"):
                            rot.subtarget = prefix + "R_" + bone.replace("L_", "")
                        elif bone.endswith("_L"):
                            rot.subtarget = prefix + bone.replace("_L", "") + "_R"
                else:
                    ConstraintSymmetry.rot_bonelist.append(bone)

            #Right side
            elif vatproperties.affected_side == 'OP2':

                #Location
                if ConstraintSymmetry.loc == "":
                    if bone.startswith("R_") or bone.endswith("_R"):
                        loc = armature.pose.bones[prefix + bone].constraints.new('COPY_LOCATION')
                        
                        #Constraint parameters
                        loc.name = "Constraint Symmetry Location"
                        loc.target = armature
                        loc.invert_x = True
                        if bone.startswith("R_"):
                            loc.subtarget = prefix + "L_" + bone.replace("R_", "")
                        elif bone.startswith("_R"):
                            loc.subtarget = prefix + bone.replace("_R", "") + "_L"
                else:
                    ConstraintSymmetry.loc_bonelist.append(bone)
                
                #Rotation
                if ConstraintSymmetry.rot == "":
                    if bone.startswith("R_") or bone.endswith("_R"):
                        rot = armature.pose.bones[prefix + bone].constraints.new('COPY_ROTATION')

                        #Constraint parameters
                        rot.name = "Constraint Symmetry Rotation"
                        rot.target = armature
                        rot.target_space = 'LOCAL'
                        rot.owner_space = 'LOCAL'
                        rot.invert_y = True
                        rot.invert_x = True
                        if bone.startswith("R_"):
                            rot.subtarget = prefix + "L_" + bone.replace("R_", "")
                        elif bone.endswith("_R"):
                            rot.subtarget = prefix + bone.replace("_R", "") + "_L"
                else:
                    ConstraintSymmetry.rot_bonelist.append(bone)

        #Deletion
        elif action == 1:
            vatproperties = bpy.context.scene.vatproperties
            armature = bpy.data.objects[vatproperties.target_armature.name]
            ConstraintSymmetry.op = 1

            #Left side
            if vatproperties.affected_side == 'OP1':

                #Location
                if ConstraintSymmetry.loc != "":
                    if bone.startswith("L_") or bone.endswith("_L"):
                        armature.pose.bones[prefix + bone].constraints.remove(ConstraintSymmetry.loc)
                else:
                    ConstraintSymmetry.loc_bonelist.append(bone)

                #Rotation
                if ConstraintSymmetry.rot != "":
                    if bone.startswith("L_") or bone.endswith("_L"):
                        armature.pose.bones[prefix + bone].constraints.remove(ConstraintSymmetry.rot)
                else:
                   ConstraintSymmetry.rot_bonelist.append(bone)

            #Right side
            elif vatproperties.affected_side == 'OP2':

                #Location
                if ConstraintSymmetry.loc != "":
                    if bone.startswith("R_") or bone.endswith("_R"):
                        armature.pose.bones[prefix + bone].constraints.remove(ConstraintSymmetry.loc)
                else:
                    ConstraintSymmetry.loc_bonelist.append(bone)

                #Rotation
                if ConstraintSymmetry.rot != "":
                    if bone.startswith("R_") or bone.endswith("_R"):
                        armature.pose.bones[prefix + bone].constraints.remove(ConstraintSymmetry.rot)
                else:
                    ConstraintSymmetry.rot_bonelist.append(bone)

    def execute(action):
        vatproperties = bpy.context.scene.vatproperties
        for bone in BoneList.symmetrical_bones:
            ConstraintSymmetry.constraint(bone, vatproperties.affected_side, action, 0)

        if BoneList.helper_bones != []:
            for bone in BoneList.helper_bones:
                ConstraintSymmetry.constraint(bone, vatproperties.affected_side, action, 1)

        #If constraints could not be applied
        if ConstraintSymmetry.loc_bonelist != []:
            if ConstraintSymmetry.op == 0:
                print("Location constraints already exist for:")
                print(ConstraintSymmetry.loc_bonelist)
            elif ConstraintSymmetry.op == 1:
                print("Location constraints not found for:")
                print(ConstraintSymmetry.loc_bonelist)
                
        if ConstraintSymmetry.rot_bonelist != []:
            if ConstraintSymmetry.op == 0:
                print("Rotation constraints already exist for:")
                print(ConstraintSymmetry.rot_bonelist)
            elif ConstraintSymmetry.op == 1:
                print("Rotation constraints not found for:")
                print(ConstraintSymmetry.rot_bonelist)

class WeightArmature: #Creates duplicate armature for more spread out weighting

    #Name container of the created weight armature
    weightarmature = ""

    def armature(action): #Creates or deletes the weight armature
        vatproperties = bpy.context.scene.vatproperties
        real_armature = bpy.data.armatures[vatproperties.target_armature.data.name]
        
        #Creation
        if action == 0:
            #Check for the armature datablock, to avoid copying it 
            try:
                real_weightarmature = bpy.data.armatures[vatproperties.target_armature.data.name + ".weight"]
            except:
                real_weightarmature = real_armature.copy()
                real_weightarmature.name = vatproperties.target_armature.data.name + ".weight"

            #Creation and link to current scene
            WeightArmature.weightarmature = bpy.data.objects.new(vatproperties.target_armature.name + ".weight", real_weightarmature)
            collection = bpy.data.collections.new("Weight Armature")
            collection.objects.link(WeightArmature.weightarmature)
            bpy.context.scene.collection.children.link(collection)

            armature = bpy.data.objects[WeightArmature.weightarmature.name]
            prefix = Prefixes.current

            #Bone connection
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT') #Apparently you're required to be in edit mode to use "data.edit_bones", else there will be no bone info given. Dumb
            armature.select_set(1)
            bpy.ops.object.mode_set(mode='EDIT')

            for bone in BoneList.symmetrical_bones:
                parent = armature.pose.bones[prefix + bone].parent.name
                if parent.count("Hand") != 0:
                    if bone.count("Finger0") != 0:
                        pass
                    else:
                        x = armature.pose.bones[prefix + bone].head.x
                        z = armature.pose.bones[prefix + bone].head.z
                        armature.data.edit_bones[parent].tail.xz = x, z
                else:
                    loc = armature.pose.bones[prefix + bone].head
                    armature.data.edit_bones[parent].tail = loc

                #Additional bone tweaking
                if bone.count("Hand") != 0:
                    y = armature.pose.bones[prefix + bone].head.y
                    armature.data.edit_bones[prefix + bone].tail.y = y

                if bone.count("Toe") != 0:
                    x = armature.pose.bones[prefix + bone].head.x
                    y = armature.pose.bones[prefix + bone].head.y
                    z = armature.pose.bones[prefix + bone].head.z

                    if bone.startswith("L_") or bone.endswith("_L"):
                        armature.data.edit_bones[prefix + bone].tail = x+0.5, y-2.5, z
                    elif bone.startswith("R_") or bone.endswith("_R"):
                        armature.data.edit_bones[prefix + bone].tail = x-0.5, y-2.5, z

                if bone.count("Finger12") != 0 or bone.count("Finger22") != 0 or bone.count("Finger32") != 0 or bone.count("Finger42") != 0:
                    x = armature.pose.bones[prefix + bone].tail.x
                    z = armature.pose.bones[prefix + bone].tail.z
                    if bone.startswith("L_") or bone.endswith("_L"):
                        armature.data.edit_bones[prefix + bone].tail.xz = x-0.1, z-0.5
                    elif bone.startswith("R_") or bone.endswith("_R"):
                        armature.data.edit_bones[prefix + bone].tail.xz = x+0.1, z-0.5

                if bone.count("Finger02") != 0:
                    y = armature.pose.bones[prefix + bone].tail.y
                    z = armature.pose.bones[prefix + bone].tail.z
                    armature.data.edit_bones[prefix + bone].tail.yz = y-0.8, z-0.4

            for bone in BoneList.central_bones:
                if bone == "Pelvis": #No parent
                    pass
                else:
                    parent = armature.pose.bones[prefix + bone].parent.name
                    loc = armature.pose.bones[prefix + bone].head
                    armature.data.edit_bones[parent].tail = loc

                #Additional bone tweaking
                if bone == "Head1":
                    x = armature.pose.bones[prefix + bone].head.x
                    y = armature.pose.bones[prefix + bone].head.y
                    z = armature.pose.bones[prefix + bone].head.z

                    armature.data.edit_bones[prefix + bone].tail = x, y, z+6

            #Final touches to the armature
            armature.data.display_type = 'OCTAHEDRAL'
            armature.data.show_bone_custom_shapes = False
            armature.show_in_front = 1

            bpy.ops.object.mode_set(mode='OBJECT')

        #Deletion    
        elif action == 1:
            bpy.data.objects.delete(WeightArmature.weightarmature.name)
        
    def execute(action):
        WeightArmature.armature(action)

class InverseKinematics: #Adds IK to the armature
    
    #Constraint checks
    ik_constraint = ""
    leftik = ""
    rightik =""

    #Variables for finish report
    op = 0
    bonelist = []

    def getconstraint(bone):
        vatproperties = bpy.context.scene.vatproperties
        armature = bpy.data.objects[vatproperties.target_armature.name]
        prefix = Prefixes.current

        #Cleans list
        InverseKinematics.bonelist = []

        try:
            InverseKinematics.ik_constraint = armature.pose.bones[prefix + bone].constraints['IK']
        except:
            InverseKinematics.ik_constraint = ""

    def IK(bone, action):
        vatproperties = bpy.context.scene.vatproperties
        armature = bpy.data.objects[vatproperties.target_armature.name]
        prefix = Prefixes.current

        InverseKinematics.getconstraint(bone)

        #Creation
        if action == 0:
            InverseKinematics.op = 0

            #Left IK
            if InverseKinematics.ik_constraint == "":
                if bone.startswith("L_") or bone.endswith("_L"):
                    ik = armature.pose.bones[prefix + bone].constraints.new('IK')
                    ik.chain_count = 3
                elif bone.startswith("R_") or bone.endswith("_R"):
                    ik = armature.pose.bones[prefix + bone].constraints.new('IK')
                    ik.chain_count = 3
            else:
                InverseKinematics.bonelist.append(bone)

        #Deletion
        elif action == 1:
            InverseKinematics.op = 1

            #Left IK
            if InverseKinematics.ik_constraint != "":
                if bone.startswith("L_") or bone.endswith("_L"):
                    armature.pose.bones[prefix + bone].constraints.remove(InverseKinematics.ik_constraint)
                elif bone.startswith("R_") or bone.endswith("_R"):
                    armature.pose.bones[prefix + bone].constraints.remove(InverseKinematics.ik_constraint)
            else:
                InverseKinematics.bonelist.append(bone)

    def execute(action):
        for bone in BoneList.symmetrical_bones:
            if bone.count("Hand") != 0 or bone.count("Foot") != 0:
                InverseKinematics.IK(bone, action)
        
        #If constraints could not be applied
        if InverseKinematics.bonelist != []:
            if InverseKinematics.op == 0:
                print("IK constraints already exist for:")
                print(InverseKinematics.bonelist)
            elif InverseKinematics.op == 1:
                print("IK constraints not found for:")
                print(InverseKinematics.bonelist)

class RigifyRetarget: #Creates animation ready rig

    #Name container of the created animation armature
    animarmature = ""

    def armature(action): #Creates or deletes the animation armature
        vatproperties = bpy.context.scene.vatproperties
        real_armature = bpy.data.armatures[vatproperties.target_armature.data.name]
        
        #Creation
        if action == 0:
            #Check for the armature datablock, to avoid copying it 
            try:
                real_animarmature = bpy.data.armatures[vatproperties.target_armature.data.name + ".anim"]
            except:
                real_animarmature = real_armature.copy()
                real_animarmature.name = vatproperties.target_armature.data.name + ".anim"

            #Creation and link to current scene
            RigifyRetarget.animarmature = bpy.data.objects.new(vatproperties.target_armature.name + ".anim", real_animarmature)
            collection = bpy.data.collections.new("Animation Armature")
            collection.objects.link(RigifyRetarget.animarmature)
            bpy.context.scene.collection.children.link(collection)

            armature = bpy.data.objects[RigifyRetarget.animarmature.name]
            prefix = Prefixes.current

            #Bone connection
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT') #Apparently you're required to be in edit mode to use "data.edit_bones", else there will be no bone info given. Dumb
            armature.select_set(1)
            bpy.ops.object.mode_set(mode='EDIT')

            for bone in BoneList.symmetrical_bones:
                parent = armature.pose.bones[prefix + bone].parent.name
                if parent.count("Hand") != 0:
                    if bone.count("Finger0") != 0:
                        pass
                    else:
                        x = armature.pose.bones[prefix + bone].head.x
                        z = armature.pose.bones[prefix + bone].head.z
                        armature.data.edit_bones[parent].tail.xz = x, z
                else:
                    loc = armature.pose.bones[prefix + bone].head
                    armature.data.edit_bones[parent].tail = loc

                #Additional bone tweaking
                if bone.count("Hand") != 0:
                    y = armature.pose.bones[prefix + bone].head.y
                    armature.data.edit_bones[prefix + bone].tail.y = y

                if bone.count("Toe") != 0:
                    x = armature.pose.bones[prefix + bone].head.x
                    y = armature.pose.bones[prefix + bone].head.y
                    z = armature.pose.bones[prefix + bone].head.z

                    if bone.startswith("L_") or bone.endswith("_L"):
                        armature.data.edit_bones[prefix + bone].tail = x+0.5, y-2.5, z
                    elif bone.startswith("R_") or bone.endswith("_R"):
                        armature.data.edit_bones[prefix + bone].tail = x-0.5, y-2.5, z

                if bone.count("Finger12") != 0 or bone.count("Finger22") != 0 or bone.count("Finger32") != 0 or bone.count("Finger42") != 0:
                    x = armature.pose.bones[prefix + bone].tail.x
                    z = armature.pose.bones[prefix + bone].tail.z
                    if bone.startswith("L_") or bone.endswith("_L"):
                        armature.data.edit_bones[prefix + bone].tail.xz = x-0.1, z-0.5
                    elif bone.startswith("R_") or bone.endswith("_R"):
                        armature.data.edit_bones[prefix + bone].tail.xz = x+0.1, z-0.5

                if bone.count("Finger02") != 0:
                    y = armature.pose.bones[prefix + bone].tail.y
                    z = armature.pose.bones[prefix + bone].tail.z
                    armature.data.edit_bones[prefix + bone].tail.yz = y-0.8, z-0.4

            for bone in BoneList.central_bones:
                if bone == "Pelvis": #No parent
                    pass
                else:
                    parent = armature.pose.bones[prefix + bone].parent.name
                    loc = armature.pose.bones[prefix + bone].head
                    armature.data.edit_bones[parent].tail = loc

                if bone == "Head1":
                    x = armature.pose.bones[prefix + bone].head.x
                    y = armature.pose.bones[prefix + bone].head.y
                    z = armature.pose.bones[prefix + bone].head.z

                    armature.data.edit_bones[prefix + bone].tail = x, y, z+6

            #Deletes unimportant bones 
            if BoneList.helper_bones != []:
                prefix = Prefixes.helper
                for bone in BoneList.helper_bones:
                    bone = armature.data.edit_bones[prefix + bone]
                    armature.data.edit_bones.remove(bone)

            if BoneList.other_bones != []:
                prefix = Prefixes.other
                for bone in BoneList.other_bones:
                    bone = armature.data.edit_bones[prefix + bone]
                    armature.data.edit_bones.remove(bone)

            #Rigify portion
            prefix = Prefixes.current

            for i in range(0,19):
                armature.data.rigify_layers.add()

            #Rigify layers
            names = ["Torso", "Torso (Tweak)", "Fingers", "Fingers (Detail)", "Arm.L (IK)", "Arm.L (FK)", "Arm.L (Tweak)", "Arm.R (IK)", "Arm.R (FK)", "Arm.R (Tweak)", "Leg.L (IK)", "Leg.L (FK)", "Leg.L (Tweak)", "Leg.R (IK)", "Leg.R (FK)", "Leg.R (Tweak)"]

            group = [3,4,6,5,2,5,4,2,5,4,2,5,4,2,5,4]

            for i, name, group in zip(range(3,19), names, group):
                armature.data.rigify_layers[i].name = name
                armature.data.rigify_layers[i].row = i
                armature.data.rigify_layers[i].group = group

            #Creates 2 pelvis bones for whatever Rigify does with em
            x = armature.pose.bones[prefix + "Pelvis"].head.x
            y = armature.pose.bones[prefix + "Pelvis"].head.y
            z = armature.pose.bones[prefix + "Pelvis"].head.z

            new_pelvis = []

            if vatproperties.scheme == 0:
                for bone in ["L_Pelvis", "R_Pelvis"]:
                    new_pelvis.append(bone)

            elif vatproperties.scheme <= 0:
                for bone in ["Pelvis_L", "Pelvis_R"]:
                    new_pelvis.append(bone)

            for bone in new_pelvis:
                ebone = armature.data.edit_bones.new(prefix + bone)

                ebone.head = armature.pose.bones[prefix + "Pelvis"].head

                #New pelvis bone positioning
                if bone.startswith("L_") or bone.endswith("_L"):
                    ebone.tail.xyz = x-3, y-2, z+4
                elif bone.startswith("R_") or bone.endswith("_R"):
                    ebone.tail.xyz = x+3, y-2, z+4

                #Rigify parameters

                #For some really dumb reason, the newly added bone is not added to the armature data until the user changes modes at least once, i know no other way around it. If you do please let me know
                bpy.ops.object.mode_set(mode='OBJECT')
                pbone = armature.pose.bones[prefix + bone]
                dbone = armature.data.bones[prefix + bone]
                bpy.ops.object.mode_set(mode='EDIT')

                pbone.rigify_type = "basic.super_copy"
                pbone.rigify_parameters.make_control = False
                dbone.layers[0] = False
                dbone.layers[3] = True

            #Symmetrical
            for bone in BoneList.symmetrical_bones:
                pbone = armature.pose.bones[prefix + bone]
                param = pbone.rigify_parameters
                dbone = armature.data.bones[prefix + bone]

                dbone.layers[0] = False

                if bone.count("Finger") != 0:
                    dbone.layers[5] = True

                if bone.count("UpperArm") != 0 or bone.count("Forearm") != 0 or bone.count("Hand") != 0:
                    if bone.startswith("L_") or bone.endswith("_L"):
                        dbone.layers[7] = True
                    elif bone.startswith("R_") or bone.endswith("_R"):
                        dbone.layers[10] = True

                if bone.count("Thigh") != 0 or bone.count("Calf") != 0 or bone.count("Foot") != 0 or bone.count("Toe") != 0:
                    if bone.startswith("L_") or bone.endswith("_L"):
                        dbone.layers[13] = True
                    elif bone.startswith("R_") or bone.endswith("_R"):
                        dbone.layers[16] = True

                if bone.count("Clavicle") != 0:
                    pbone.rigify_type = "basic.super_copy"
                    param.make_widget = False
                    dbone.layers[3] = True

                if bone.count("UpperArm") != 0:
                    pbone.rigify_type = "limbs.super_limb"
                    param.tweak_layers[1] = False
                    param.tweak_layers[8] = True
                    param.fk_layers[1] = False
                    param.fk_layers[9] = True

                if bone.count("Thigh") != 0:
                    pbone.rigify_type = "limbs.super_limb"
                    param.limb_type = 'leg'
                    param.tweak_layers[1] = False
                    param.tweak_layers[15] = True
                    param.fk_layers[1] = False
                    param.fk_layers[14] = True

            #Central
            for bone in BoneList.central_bones:
                pbone = armature.pose.bones[prefix + bone]
                param = pbone.rigify_parameters
                dbone = armature.data.bones[prefix + bone]

                dbone.layers[0] = False
                dbone.layers[3] = True

                if bone.count("Pelvis") != 0:
                    pbone.rigify_type = "spines.basic_spine"
                    param.pivot_pos = 2
                    param.tweak_layers[1] = False
                    param.tweak_layers[4] = True
                    param.fk_layers[1] = False
                    param.fk_layers[4] = True

                if bone.count("Neck1") != 0:
                    pbone.rigify_type = "spines.super_head"
                    param.connect_chain = True
                    param.tweak_layers[1] = False
                    param.tweak_layers[4] = True

            #Final touches to the armature
            armature.data.display_type = 'OCTAHEDRAL'
            armature.data.show_bone_custom_shapes = False

            bpy.ops.object.mode_set(mode='OBJECT')

        #Deletion    
        elif action == 1:
            bpy.data.objects.delete(RigifyRetarget.animarmature.name)
        
    def execute(action):
        RigifyRetarget.armature(action)
