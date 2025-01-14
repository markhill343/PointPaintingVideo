import os
import cv2
import numpy as np
import json

class Calibration:
    """
        Perform different types of calibration between camera & LIDAR
        image = Projection * Camera3D_after_rectification
        image = Projection * R_Rectification * Camera3D_reference
    """
    def __init__(self, calib_path, P2, R0_rect, from_video=False, from_json=False):
        self.P2 = P2
        self.R0_rect = R0_rect
        self.calib_path = calib_path
        self.calib_matrix = {}
        if from_video:
            self.calib_matrix = self.parse_calib_from_video(calib_path)
            self.calib_path = os.path.join(calib_path, "modified_calib_file.txt")
            print('#################', self.calib_path)
        elif from_json:
            self.calib_matrix = self.parse_calib_from_json(calib_path)
        else:
            self.calib_matrix = self.parse_calib_files(calib_path)

        # Projection Matrix (Intrensic) .. from camera 3d (after rectification) to image coord.
        self.P2 = P2
        # rectification rotation matrix 3x3
        self.R0_rect = R0_rect
        # Extrensic Transilation-Rotation Matrix from LIDAR to Cam ref(before rectification)
        self.Tr_velo_to_cam = self.calib_matrix["Tr_velo_to_cam"].reshape(3,4)

    def parse_calib_files(self, calib_path):
        assert self.calib_path is not None

        mat_ = {}
        with open(os.path.join(calib_path), 'r') as calib_file:
            for line in calib_file:
                line = line.split()
                # Avoiding empty line exception
                if len(line) == 0:
                    continue
                # The only non-float values in these files are dates, which
                # we don't care about anyway
                try: 
                    mat_[line[0][:-1]] = np.array(line[1:], dtype=np.float32)
                except ValueError:
                    continue

        return mat_

    def parse_calib_from_video(self, calib_path):
        """ Read calibration for camera 2 from video calib files.
            there are calib_cam_to_cam and calib_velo_to_cam under the calib_root_dir
        """
        assert calib_path is not None

        mat_ = {}
        cam2cam = self.parse_calib_files(
            os.path.join(calib_path, "calib_cam_to_cam.txt")
        )
        velo2cam = self.parse_calib_files(
            os.path.join(calib_path, "calib_velo_to_cam.txt")
        )


        mat_["P0"] = cam2cam["P_rect_00"]
        mat_["P1"] = cam2cam["P_rect_01"]
        mat_["P2"] = cam2cam["P_rect_02"]
        mat_["P3"] = cam2cam["P_rect_03"]

        mat_["R0_rect"] = cam2cam["R_rect_00"]

        Tr_velo_to_cam = np.zeros((3, 4))
        Tr_velo_to_cam[0:3, 0:3] = np.reshape(velo2cam["R"], [3, 3])
        Tr_velo_to_cam[:, 3] = velo2cam["T"]
        mat_["Tr_velo_to_cam"] = Tr_velo_to_cam
        return mat_
    
    def parse_calib_from_json(self, json_path):

        with open(json_path, 'r') as json_file:
            json_data = json.load(json_file)

        mat_ = {}

        # Extract Tr_velo_to_cam from Json data
        extrinsic_data = json_data['top_center_lidar-to-center_camera-extrinsic']['param']['sensor_calib']['data']
        Tr_velo_to_cam = np.array(extrinsic_data, dtype=np.float32)

        # Set Tr_velo_to_cam as a 3x4 matrix
        mat_["Tr_velo_to_cam"] = Tr_velo_to_cam[:3, :]

        return mat_
