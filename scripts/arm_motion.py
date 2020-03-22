import support.vrep as vrep
import time
import numpy as np
import math
from scipy.linalg import expm,logm

absolute_position = -1

# ======================================= Helper Functions ============================================== #
class arm_motion:
    """ Class for the 2D motion of the entire robot frame. """

    def __init__(self, clientID, youBotRef, arms, youBot, gripper):
        """ Initialize a motion object. """
        self.clientID = clientID
        self.youBotRef = youBotRef
        self.youBot = youBot
        self.arms = arms
        self.gripper = gripper

        # forward kinematics for arm joints
        # zero position, relative to youBot frame
        self.w = np.array([[1,0,0],[0,1,0],[0,1,0],[0,1,0],[1,0,0]])
        self.r = []
        self.v = []
        self.SetJointPosition([0,0,0,0,0])
        for arm, w in zip(self.arms,self.w):
            r = self.get_any_ref_position(arm, self.youBot)
            self.r.append(r)
            self.v.append(np.cross(-w,r))
        pos = self.get_any_ref_position(gripper, self.youBot)
        self.M = np.array([[-1,0,0,pos[0]],[0,0,1,pos[1]],[0,1,0,pos[2]],[0,0,0,1]])

    def get_any_ref_position(self, handle, reference):
        error,position = vrep.simxGetObjectPosition(self.clientID, handle, reference, vrep.simx_opmode_blocking)
        if error:
            print("get_global_position ERROR")
        print("POSITION: x="+str(position[0])+" y="+str(position[1])+" z="+str(position[2])+"\n")
        return position

    def forw_kin(self, thetas):
        e_s_theta = []
        for w, v, theta in zip(self.w,self.v,thetas):
            w_skew = np.array([[0,-w[2],w[1]], [w[2],0,-w[0]], [-w[1],w[0],0]])
            temp = np.eye(3) + np.sin(theta)*w_skew + (1-np.cos(theta))*(w_skew@w_skew)
            temp2 = (np.eye(3)*theta + (1-np.cos(theta))*w_skew + \
                    (theta-np.sin(theta))*(w_skew@w_skew))@v

            temp3 = np.zeros((4,4))
            temp3[0:3, 0:3] = temp
            temp3[0:3, 3] = temp2
            temp3[3, 3] = 1
            e_s_theta.append(temp3)

        answer = e_s_theta[0]
        for i in range(1, len(e_s_theta)):
            answer = answer@e_s_theta[i]
        answer = answer@self.M
        return answer

    def SetJointPosition(self, thetas):
        for arm, theta in zip(self.arms, thetas):
            vrep.simxSetJointPosition(self.clientID, arm, theta, vrep.simx_opmode_blocking)
