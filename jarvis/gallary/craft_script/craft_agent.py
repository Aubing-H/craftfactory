import time
import random
import math
import os 
import cv2
import re
import torch
import av
import ray
import rich
from rich.console import Console
from tqdm import tqdm
import uuid
import json
import hydra
import random
import numpy as np
from pathlib import Path
from typing import (
    Sequence, List, Mapping, Dict, 
    Callable, Any, Tuple, Optional, Union
)
from jarvis.stark_tech.ray_bridge import MinecraftWrapper
from jarvis.assets import RECIPES_INGREDIENTS
from jarvis.gallary.utils.rollout import Recorder

CAMERA_SCALER = 360.0 / 2400.0
WIDTH, HEIGHT = 640, 360

def random_dic(dicts):
    dict_key_ls = list(dicts.keys())
    random.shuffle(dict_key_ls)
    new_dic = {}
    for key in dict_key_ls:
        new_dic[key] = dicts.get(key)
    return new_dic

def write_video(
    file_name: str, 
    frames: List[np.ndarray], 
    width: int = 640, 
    height: int = 360, 
    fps: int = 20
) -> None:
    """Write video frames to video files. """
    with av.open(file_name, mode="w", format='mp4') as container:
        stream = container.add_stream("h264", rate=fps)
        stream.width = width
        stream.height = height
        for frame in frames:
            frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
            for packet in stream.encode(frame):
                    container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


'''
KEY_POS_INVENTORY_WO_RECIPE
KEY_POS_INVENTORY_WO_RECIPE
KEY_POS_TABLE_WO_RECIPE
KEY_POS_TABLE_W_RECIPE
'''
KEY_POS_INVENTORY_WO_RECIPE = {
    'resource_slot': {
        'left-top': (329, 114), 
        'right-bottom': (365, 150), 
        'row': 2, 
        'col': 2,
        'prefix': 'resource', 
        'start_id': 0, 
    },
    'result_slot': {
        'left-top': (385, 124), 
        'right-bottom': (403, 142),
        'row': 1, 
        'col': 1,
        'prefix': 'result', 
        'start_id': 0, 
    },
    'hotbar_slot': {
        'left-top': (239, 238), 
        'right-bottom': (401, 256),
        'row': 1, 
        'col': 9, 
        'prefix': 'inventory', 
        'start_id': 0, 
    }, 
    'inventory_slot': {
        'left-top': (239, 180), 
        'right-bottom': (401, 234), 
        'row': 3, 
        'col': 9,
        'prefix': 'inventory',
        'start_id': 9,
    }, 
    'recipe_slot': {
        'left-top': (336, 158),
        'right-bottom': (356, 176),
        'row': 1, 
        'col': 1,
        'prefix': 'recipe', 
        'start_id': 0,
    }
}

KEY_POS_INVENTORY_W_RECIPE = {
    'resource_slot': {
        'left-top': (406, 114), 
        'right-bottom': (442, 150), 
        'row': 2, 
        'col': 2,
        'prefix': 'resource', 
        'start_id': 0, 
    },
    'result_slot': {
        'left-top': (462, 124), 
        'right-bottom': (480, 142),
        'row': 1, 
        'col': 1,
        'prefix': 'result', 
        'start_id': 0, 
    },
    'hotbar_slot': {
        'left-top': (316, 238), 
        'right-bottom': (478, 256),
        'row': 1, 
        'col': 9, 
        'prefix': 'inventory', 
        'start_id': 0, 
    }, 
    'inventory_slot': {
        'left-top': (316, 180), 
        'right-bottom': (478, 234), 
        'row': 3, 
        'col': 9,
        'prefix': 'inventory',
        'start_id': 9, 
    }, 
    'recipe_slot': {
        'left-top': (413, 158),
        'right-bottom': (433, 176),
        'row': 1, 
        'col': 1,
        'prefix': 'recipe', 
        'start_id': 0,
    }
}

KEY_POS_TABLE_WO_RECIPE = {
    'resource_slot': {
        'left-top': (261, 113), 
        'right-bottom': (315, 167), 
        'row': 3, 
        'col': 3,
        'prefix': 'resource', 
        'start_id': 0, 
    },
    'result_slot': {
        'left-top': (351, 127), 
        'right-bottom': (377, 153),
        'row': 1, 
        'col': 1,
        'prefix': 'result', 
        'start_id': 0, 
    },
    'hotbar_slot': {
        'left-top': (239, 238), 
        'right-bottom': (401, 256),
        'row': 1, 
        'col': 9, 
        'prefix': 'inventory', 
        'start_id': 0, 
    }, 
    'inventory_slot': {
        'left-top': (239, 180), 
        'right-bottom': (401, 234), 
        'row': 3, 
        'col': 9,
        'prefix': 'inventory',
        'start_id': 9,
    }, 
    'recipe_slot': {
        'left-top': (237, 131),
        'right-bottom': (257, 149),
        'row': 1, 
        'col': 1,
        'prefix': 'recipe', 
        'start_id': 0,
    }
}

KEY_POS_TABLE_W_RECIPE = {
    'resource_slot': {
        'left-top': (338, 113), 
        'right-bottom': (392, 167), 
        'row': 3, 
        'col': 3,
        'prefix': 'resource', 
        'start_id': 0, 
    },
    'result_slot': {
        'left-top': (428, 127), 
        'right-bottom': (454, 153),
        'row': 1, 
        'col': 1,
        'prefix': 'result', 
        'start_id': 0, 
    },
    'hotbar_slot': {
        'left-top': (316, 238), 
        'right-bottom': (478, 256),
        'row': 1, 
        'col': 9, 
        'prefix': 'inventory', 
        'start_id': 0, 
    }, 
    'inventory_slot': {
        'left-top': (316, 180), 
        'right-bottom': (478, 234), 
        'row': 3, 
        'col': 9,
        'prefix': 'inventory',
        'start_id': 9,
    }, 
    'recipe_slot': {
        'left-top': (314, 131),
        'right-bottom': (334, 149),
        'row': 1, 
        'col': 1,
        'prefix': 'recipe', 
        'start_id': 0,
    }
}

def COMPUTE_SLOT_POS(KEY_POS):
    result = {}
    for k, v in KEY_POS.items():
        left_top = v['left-top']
        right_bottom = v['right-bottom']
        row = v['row']
        col = v['col']
        prefix = v['prefix']
        start_id = v['start_id']
        width = right_bottom[0] - left_top[0]
        height = right_bottom[1] - left_top[1]
        slot_width = width // col
        slot_height = height // row
        slot_id = 0
        for i in range(row):
            for j in range(col):
                result[f'{prefix}_{slot_id + start_id}'] = (
                    left_top[0] + j * slot_width + (slot_width // 2), 
                    left_top[1] + i * slot_height + (slot_height // 2),
                )
                slot_id += 1
    return result

SLOT_POS_INVENTORY_WO_RECIPE = COMPUTE_SLOT_POS(KEY_POS_INVENTORY_WO_RECIPE)
SLOT_POS_INVENTORY_W_RECIPE = COMPUTE_SLOT_POS(KEY_POS_INVENTORY_W_RECIPE)
SLOT_POS_TABLE_WO_RECIPE = COMPUTE_SLOT_POS(KEY_POS_TABLE_WO_RECIPE)
SLOT_POS_TABLE_W_RECIPE = COMPUTE_SLOT_POS(KEY_POS_TABLE_W_RECIPE)

def exception_exit(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            exit()
    return wrapper

# @ray.remote(max_restarts=-1, max_task_retries=-1)
class Worker(object):
    
    def __init__(
        self, 
        env: Union[str, MinecraftWrapper],
        sample_ratio: float = 0.5,
        inventory_slot_range: Tuple[int, int] = (0, 36), 
        **kwargs, 
    )-> None:
        # print("Initializing worker...")
        self.sample_ratio = sample_ratio
        self.inventory_slot_range = inventory_slot_range
    
        if isinstance(env, str):
            self.env = MinecraftWrapper(env)
            self.reset()
        else:
            self.env = env
            self.reset(fake_reset=True)
        
    
    @exception_exit
    def reset(self, fake_reset: bool = False):
        self.outframes = []
        self.outactions = []
        self.outinfos = []
        self.resource_record = {f'resource_{x}': {'type': 'none', 'quantity': 0} for x in range(9)}

        if not fake_reset:
            self.obs, self.info = self.env.reset()
            self.outframes.append(self.info['pov'].astype(np.uint8))
            self.info['resource'] = self.resource_record
            self.outinfos.append(self.info)

        if hasattr(self, 'current_gui_type') and self.current_gui_type:
            if self.current_gui_type == 'inventory_w_recipe':
                self.move_to_slot(SLOT_POS_INVENTORY_W_RECIPE, 'recipe_0')
                self._select_item()
            elif self.current_gui_type == 'crating_table_w_recipe':
                self.move_to_slot(SLOT_POS_TABLE_W_RECIPE, 'recipe_0')
                self._select_item()
                
            if self.info['is_gui_open']:
                self._call_func('inventory')
        
        self.current_gui_type = None
        self.cursor_slot = 'none'
        self.crafting_slotpos = 'none'
        self._null_action(1)

    def _assert(self, condition, message=None):
        if not condition:
            raise AssertionError(message)
        
    def _step(self, action):
        self.obs, _, _, _, self.info = self.env.step(action)
        self.outframes.append(self.info['pov'].astype(np.uint8))
        self.info['resource'] = self.resource_record
        self.outinfos.append(self.info)
        self.outactions.append(dict(action))
        return self.obs, _, _, _, self.info

    def open_inventory_wo_recipe(self):
        self.cursor = [WIDTH // 2, HEIGHT // 2]
        self._call_func('inventory')
        self.current_gui_type = 'inventory_wo_recipe'
    
    def open_inventory_w_recipe(self):
        self.open_inventory_wo_recipe()
        self.move_to_slot(SLOT_POS_INVENTORY_WO_RECIPE, 'recipe_0')
        self._select_item()
        self.current_gui_type = 'inventory_w_recipe'
    
    def open_crating_table_wo_recipe(self):

        # if self.current_gui_type:
        #     labels=self.get_labels()
        #     inventory_id = self.find_in_inventory(labels, 'crafting_table')
        #     self._assert(inventory_id, f"no crafting_table")
        # else:
        #     self.current_gui_type = 'inventory_wo_recipe'
        #     labels=self.get_labels()
        #     inventory_id = self.find_in_inventory(labels, 'crafting_table')
        #     self._assert(inventory_id, f"no crafting_table")
        #     self.current_gui_type = None

        # if not self.current_gui_type:
        #     self.open_inventory_wo_recipe()
        #     slot_pos = SLOT_POS_INVENTORY_WO_RECIPE
        # else:
        #     if not 'wo' in self.current_gui_type:
        #         slot_pos = SLOT_POS_INVENTORY_W_RECIPE
        #     else:
        #         slot_pos = SLOT_POS_INVENTORY_WO_RECIPE
        # if inventory_id != 'inventory_0':
        #     if labels['inventory_0']['type'] != 'none':
        #         for i in range(4):
        #             del labels["resource_"+str(i)]
        #         inventory_id_none = self.find_in_inventory(labels, 'none')
        #         self.pull_item(slot_pos, 'inventory_0', inventory_id_none)
        #         self._null_action(2)
        #     self.pull_item(slot_pos, inventory_id, 'inventory_0')
        # self._call_func('inventory')
        self._place_down()
        self.cursor = [WIDTH // 2, HEIGHT // 2]
        self._call_func('use')
        self.current_gui_type = 'crating_table_wo_recipe'
    
    def open_crating_table_w_recipe(self):
        self.open_crating_table_wo_recipe()
        self.move_to_slot(SLOT_POS_TABLE_WO_RECIPE, 'recipe_0')
        self._select_item()
        self.current_gui_type = 'crating_table_w_recipe'

    def _call_func(self, func_name: str):
        action = self.env.noop_action()
        action[func_name] = 1
        for i in range(1):
            self.obs, _, _, _, self.info = self._step(action)
        action[func_name] = 0
        for i in range(5):
            self.obs, _, _, _, self.info = self._step(action)

    def _look_down(self):
        action = self.env.noop_action()
        for i in range(1):
            action['camera'] = np.array([88, 0])
        self.obs, _, _, _, self.info = self._step(action)
    
    def _jump(self):
        self._call_func('jump')
    
    def _place_down(self):
        self._look_down()
        self._jump()
        self._call_func('use')

    def _use_item(self):
        self._call_func('use')
    
    def _select_item(self):
        self._call_func('attack')

    def _null_action(self, times=1):
        action = self.env.noop_action()
        for i in range(times):
            self.obs, _, _, _, self.info = self._step(action)
    
    def _attack_continue(self, times=1):
        action = self.env.noop_action()
        action['attack'] = 1
        for i in range(times):
            self.obs, _, _, _, self.info = self._step(action)
    
    def _palce_continue(self, times=1):
        action = self.env.noop_action()
        action['use'] = 1
        for i in range(1):
            self.obs, _, _, _, self.info = self._step(action)
        action['use'] = 0
        for i in range(1):
            self.obs, _, _, _, self.info = self._step(action)

    def move_with_order3(self, dl: float, dt: int):
        ''' the velocity is a curve, acceleraty come from a0 to -a0 '''
        assert dt > 0, f'dt: {dt} can not be zero or negitive'
        assert dl < 60. * dt, f'too fast with len: {dl}, t: {dt}, mx=60'
        a0 = 6*dl / dt**2
        s = 0.
        for t in range(1, dt + 1):
            x = a0 * t**2 * (3 - 2*t/dt) / 6
            yield x - s
            s = x

    def move_with_order2(self, dl: float, dt: int):
        ''' the velocity is a broken line, acceleraty = a0 then turn to -a0 '''
        assert dt > 0, f'dt: {dt} can not be zero or negitive'
        assert dl < 45. * dt, f'too fast with len: {dl}, t: {dt}, mx=45'
        a0 = 4*dl / dt**2
        s = 0.
        for t in range(1, dt + 1):
            x = a0 * t**2 / 2 if t <= dt/2 else \
                a0*dt*t - dl - a0 * t**2 / 2
            yield x - s
            s = x

    def move_to_pos(self, x: float, y: float, step_rg=(10, 20)):
        camera_x = x - self.cursor[0]
        camera_y = y - self.cursor[1]

        step_s =  max(math.ceil(abs(camera_x / 60.)), 
                     math.ceil(abs(camera_y / 60.)))
        if step_rg[0] < step_s:
            step_rg[0] = step_s
        if step_rg[1] <= step_s:
            step_rg[1] = step_s + 1
        num_steps= np.random.randint(*step_rg)

        for dx, dy in zip(self.move_with_order3(camera_x, num_steps), 
                          self.move_with_order3(camera_y, num_steps)):
            self.action_once(dx, dy)

    def move_to_pos_fast(self, x: float, y: float):
        max_yaw_step, max_pitch_step = 180., 90.
        camera_x = x - self.cursor[0]  # W
        camera_y = y - self.cursor[1]  # H
        min_step = math.ceil(max(abs(camera_x)/max_yaw_step, 
                                 abs(camera_y)/max_pitch_step))
        for _ in range(min_step):
            dx, dy = camera_x / min_step, camera_y / min_step
            self.action_once(dx, dy)

    def random_move_or_stay(self, max=20, ismove=False):
        if not ismove:
            if np.random.uniform(0, 1) > 0.25:
                num_random = random.randint(1,4)
                if np.random.uniform(0, 1) > 0.5:
                    for i in range(num_random):
                        self.action_once(0, 0)
                else:
                    for i in range(num_random):
                        d1 =  np.random.uniform(-max, max)
                        d2 =  np.random.uniform(-max, max)
                        self.action_once(d1, d2)
            else:
                pass
        else:
            if np.random.uniform(0, 1) > 0.5:
                num_random = random.randint(2, 4)
                for i in range(num_random):
                    d1 =  np.random.uniform(-max, max)
                    d2 =  np.random.uniform(-max, max)
                    self.action_once(d1, d2)
            else:
                pass

    def action_once(self, x: float, y: float):
        action = self.env.noop_action() 
        px, py = self.cursor[0] + x, self.cursor[1] + y
        if (px < 0. or px > 640.) or (py < 0. or py > 360.):
            return # do nothing
        action['camera'] = np.array([y * CAMERA_SCALER, x * CAMERA_SCALER])
        self.obs, _, _, _, self.info = self._step(action) 
        self.cursor[0] = px
        self.cursor[1] = py
    
    def move_to_slot(self, SLOT_POS: Dict, slot: str):
        self._assert(slot in SLOT_POS, f'Error: slot: {slot}')
        x, y = SLOT_POS[slot]
        self.move_to_pos(x, y)
        self.cursor_slot = slot

    def pull_item(self, 
        SLOT_POS: Dict, 
        item_from: str, 
        item_to: str
    ) -> None:
        if 'resource' in item_to:
            item = self.info['inventory'][int(item_from.split('_')[-1])]
            self.resource_record[item_to] = item
        self.move_to_slot(SLOT_POS, item_from)
        # self._null_action(1) 
        self._select_item()
        self.move_to_slot(SLOT_POS, item_to)
        # self._null_action(1) 
        self._use_item()

    def pull_items(self, 
        SLOT_POS: Dict, 
        target_num: int,
        item_from: str, 
        item_to: str
    ) -> None:
        self.move_to_slot(SLOT_POS, item_from)
        # self._null_action(1) 
        for i in range(target_num+1):
            self._select_item()
        self.move_to_slot(SLOT_POS, item_to) 
        self._select_item()
        self._null_action(10)

    def pull_item_continue(self, 
        SLOT_POS: Dict, 
        item_to: str,
        item: str 
    ) -> None:
        if 'resource' in item_to:
            self.resource_record[item_to] = item
        self.move_to_slot(SLOT_POS, item_to)
        self._use_item()

    def pull_item_return(self, 
        SLOT_POS: Dict, 
        item_to: str,
    ) -> None: 
        self.move_to_slot(SLOT_POS, item_to)
        # self._null_action(1) 
        self._select_item()
          
    
    def get_labels(self):
        result = {}
        # generate resource recording item labels
        if 'table' in self.current_gui_type:
            num_slot = 9
        else:
            num_slot = 4
        for i in range(num_slot):
            slot = f'resource_{i}'
            item = self.resource_record[slot]
            result[slot] = item
        
        # generate inventory item labels
        for slot, item in self.info['inventory'].items():
            result[f'inventory_{slot}'] = item
        
        result['cursor_slot'] = self.cursor_slot
        result['gui_type'] = self.current_gui_type
        result['equipped_items'] = { k: v['type'] for k, v in self.info['equipped_items'].items()}
        
        return result
    
    def crafting(self, target: str, target_num: int=1, is_recipe=False, close_inventory=False, first=0):
        try:
            cur_path = os.path.abspath(os.path.dirname(__file__))
            root_path = cur_path[:cur_path.find('jarvis')]
            relative_path = os.path.join("jarvisbase/jarvis/assets/recipes", target + '.json')
            recipe_json_path = os.path.join(root_path, relative_path)
            with open(recipe_json_path) as file:
                recipe_info = json.load(file)

            if first:
                need_table = 1
                self.cursor = [WIDTH // 2, HEIGHT // 2]
                self.current_gui_type = 'crating_table_wo_recipe'
                self.crafting_slotpos = SLOT_POS_TABLE_WO_RECIPE
            else:
                need_table = 1

            random_x, random_y = np.random.random() * 640., np.random.random() * 360.
            self.move_to_pos_fast(random_x, random_y)
            # crafting
            if recipe_info.get('result').get('count'):
                iter_num = math.ceil(target_num / int(recipe_info.get('result').get('count')))
            else:
                iter_num = target_num
            print(f"need {iter_num} crafting to get {target_num} {target}")
            self.crafting_once(target, iter_num, recipe_info, need_table)

            # close inventory
            if close_inventory:
                self._call_func('inventory')
                if need_table:
                    self.return_crafting_table()
                self.current_gui_type = None

        except AssertionError as e:
            return False, str(e) 
        
        return True, None

        
    def return_crafting_table(self):
        for i in range(20):
            self._attack_continue(10)
            labels = self.get_labels()
            if self.find_in_inventory(labels, 'crafting_table'):
                break
        labels = self.get_labels()
        self._assert(self.find_in_inventory(labels, 'crafting_table'), f'return crafting_table unsuccessfully')    
    
    # crafting_table / inventory
    def crafting_type(self, target_data: Dict):
        if 'pattern' in target_data:
            pattern = target_data.get('pattern')
            col_len = len(pattern)
            row_len = len(pattern[0])
            if col_len <= 2 and row_len <= 2:
                return False
            else:
                return True
        else:
            ingredients = target_data.get('ingredients')
            item_num = len(ingredients)
            if item_num <= 4:
                return False
            else:
                return True
    
    # search item in agent's inventory 
    def find_in_inventory(self, labels: Dict, item: str, item_type: str='item', path=None):

        if path == None:
            path = []
        for key, value in labels.items():
            current_path = path + [key]
            if item_type == "item":
                if re.match(item, str(value)):
                    return current_path
                elif isinstance(value, dict):
                    result = self.find_in_inventory(value, item, item_type, current_path)
                    if result is not None:
                        return result[0]
            elif item_type == "tag":
                # tag info
                cur_path = os.path.abspath(os.path.dirname(__file__))
                root_path = cur_path[:cur_path.find('jarvis')]
                relative_path = os.path.join("jarvisbase/jarvis/assets/tag_items.json")
                tag_json_path = os.path.join(root_path, relative_path)
                with open(tag_json_path) as file:
                    tag_info = json.load(file)

                item_list = tag_info['minecraft:'+item]
                for i in range(len(item_list)):
                    if re.match(item_list[i][10:], str(value)):
                        return current_path
                    elif isinstance(value, dict):
                        result = self.find_in_inventory(value, item, item_type, current_path)
                        if result is not None:
                            return result[0]
        return None

    # crafting once 
    def crafting_once(self, target: str, iter_num: int, recipe_info: Dict, is_crafting_table: bool):

        # shaped crafting
        if "pattern" in recipe_info:
            self.crafting_shaped(target, iter_num, recipe_info)
        # shapless crafting
        else:
            self.crafting_shapeless(target, iter_num, recipe_info)
            
        # get result
        # Do not put the result in resource_0-4/9 & resource_0-4   
        labels = self.get_labels()
        if is_crafting_table:
            for i in range(9):
                del labels["resource_"+str(i)]
        else:
            for i in range(4):
                del labels["resource_"+str(i)]
        for i in range(9):
            del labels["inventory_"+str(i)]
        # if tagret exists, stack it
        result_inventory_id_1 = self.find_in_inventory(labels, target)

        if result_inventory_id_1:
            item_num = labels.get(result_inventory_id_1).get('quantity')
            self.pull_items(self.crafting_slotpos, iter_num, 'result_0', result_inventory_id_1)
            labels_after = self.get_labels()
            item_num_after = labels_after.get(result_inventory_id_1).get('quantity')
            if item_num == item_num_after:
                result_inventory_id_2 = self.find_in_inventory(labels, 'none')
                self._assert(result_inventory_id_2, f"no space to place result")
                self.pull_item_continue(self.crafting_slotpos, result_inventory_id_2, target)
                # check result
                self._assert(self.get_labels().get(result_inventory_id_2).get('type') == target, f"fail for unkown reason") 
        else:
            result_inventory_id_2 = self.find_in_inventory(labels, 'none')
            self._assert(result_inventory_id_2, f"no space to place result")
            self.move_to_slot(self.crafting_slotpos, 'result_0')
            self.pull_items(self.crafting_slotpos, iter_num, 'result_0', result_inventory_id_2)
            self._assert(self.get_labels().get(result_inventory_id_2).get('type') == target, f"fail for unkown reason")
        # clear resource          
        self.resource_record =  {f'resource_{x}': {'type': 'none', 'quantity': 0} for x in range(9)}
        # self._null_action(2)

    # shaped crafting
    def crafting_shaped(self, target:str, iter_num:int, recipe_info: Dict):
        slot_pos = self.crafting_slotpos
        labels = self.get_labels()
        pattern = recipe_info.get('pattern')
        items = recipe_info.get('key')
        items = random_dic(items)
        # place each item in order
        for k, v in items.items():
            signal = k
            if v.get('item'):
                item = v.get('item')[10:]
                item_type= 'item'
            else:
                item = v.get('tag')[10:]
                item_type= 'tag'

            inventory_id = self.find_in_inventory(labels, item, item_type)
            self._assert(inventory_id, f"not enough {item}")
            inventory_num = labels.get(inventory_id).get('quantity')

            # clculate the amount needed
            num_need = 0
            for i in range(len(pattern)):
                for j in range(len(pattern[i])):
                    if pattern[i][j] == signal:
                        num_need += 1
            num_need = num_need * iter_num
            self._assert(num_need <= inventory_num, f"not enough {item}")

            # place
            self.random_move_or_stay(max=50)
            
            resource_idx = 0
            first_pull = 1
            if 'table' in self.current_gui_type:
                type = 3
            else:
                type = 2
            for i in range(len(pattern)):
                resource_idx = i * type
                for j in range(len(pattern[i])):
                    if pattern[i][j] == signal:
                        if first_pull:
                            self.pull_item(slot_pos, inventory_id, 'resource_' + str(resource_idx))
                            for i in range(iter_num-1):
                                self._use_item()
                                self._null_action(1)
                            first_pull = 0
                        else:
                            self.pull_item_continue(slot_pos, 'resource_' + str(resource_idx), item)
                            for i in range(iter_num-1):
                                self._use_item()
                                self._null_action(1)
                    resource_idx += 1

            # return the remaining items
            if num_need < inventory_num:
                self.pull_item_return(slot_pos, inventory_id)

    
    # shapeless crafting
    def crafting_shapeless(self, target:str, iter_num:int, recipe_info: Dict):   
        slot_pos = self.crafting_slotpos 
        labels = self.get_labels()
        ingredients = recipe_info.get('ingredients')
        random.shuffle(ingredients)
        items = dict()
        items_type = dict()

        # clculate the amount needed and store <item, quantity> in items
        for i in range(len(ingredients)):
            if ingredients[i].get('item'):
                item = ingredients[i].get('item')[10:]
                item_type = 'item'
            else:
                item = ingredients[i].get('tag')[10:]
                item_type = 'tag'
            items_type[item] = item_type
            if items.get(item):
                items[item] += 1
            else:
                items[item] = 1
        
        # place each item in order
        resource_idx = 0
        for item, num_need in items.items():
            self.random_move_or_stay(max=50)
            inventory_id = self.find_in_inventory(labels, item, items_type[item])
            self._assert(inventory_id, f"not enough {item}")
            inventory_num = labels.get(inventory_id).get('quantity')
            self._assert(num_need <= inventory_num, f"not enough {item}")

            # place 
            num_need -= 1
            self.pull_item(slot_pos, inventory_id, 'resource_' + str(resource_idx))
            for i in range(iter_num-1):
                self._use_item()
                self._null_action(1)
            resource_idx += 1
            if num_need != 0:
                for i in range(num_need):
                    self.pull_item_continue(slot_pos, 'resource_' + str(resource_idx), item)
                    for i in range(iter_num-1):
                        self._use_item()
                        self._null_action(1)
                    resource_idx += 1
            num_need = (num_need + 1) * iter_num
            # return the remaining items
            if inventory_num > (num_need + 1):
                self.pull_item_return(slot_pos, inventory_id)

def test_one():
    worker = Worker('test')
    worker.crafting('stick', 1, first=1)
    worker.crafting('wooden_pickaxe', 1, first=0)
    write_video(f'/data1/houjinbing/project/minerl/jarvisbase/jarvis/gallary/craft_script/wooden_pickaxe.mp4', worker.outframes)

if __name__ == '__main__':
    # worker = Worker('test')
    # worker.crafting('crafting_table', 2)
    # write_video('/data1/houjinbing/project/minerl/jarvisbase/jarvis/gallary/craft_script/test.mp4', worker.outframes)
    test_one()