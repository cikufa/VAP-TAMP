"""Regression checks for real geometry and process-containment invariants."""
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vlm-tamp'))
sys.path.insert(0, str(ROOT / 'scripts'))
from primitive_compat import sample_aabb_side, navigation_target_rooms
from native_runtime import apply_cpu_affinity


class RuntimeGeometry(unittest.TestCase):
    def test_carried_object_uses_current_room_instead_of_cached_origin(self):
        obj = SimpleNamespace(fixed_base=False, in_rooms=['garden_0'],
                              get_position=lambda: np.array([2., 3., .14]))
        room_map = SimpleNamespace(get_room_instance_by_point=lambda xy: 'kitchen_0')
        self.assertEqual(navigation_target_rooms(obj, room_map, np.zeros(3)), ['kitchen_0'])
        self.assertEqual(obj.in_rooms, ['garden_0'])

    def test_fixed_floor_retains_its_annotated_rooms(self):
        obj = SimpleNamespace(fixed_base=True, in_rooms=['kitchen_0', 'hall_0'])
        room_map = SimpleNamespace(get_room_instance_by_point=lambda xy: 'garden_0')
        self.assertEqual(navigation_target_rooms(obj, room_map, np.zeros(3)),
                         ['kitchen_0', 'hall_0'])

    def test_unmapped_movable_object_does_not_reuse_stale_room(self):
        obj = SimpleNamespace(fixed_base=False, in_rooms=['garden_0'],
                              get_position=lambda: np.zeros(3))
        room_map = SimpleNamespace(get_room_instance_by_point=lambda xy: None)
        self.assertEqual(navigation_target_rooms(obj, room_map, np.zeros(3)), [None])

    def test_floor_and_small_object_samples_lie_on_actual_side_faces(self):
        state = np.random.get_state()
        try:
            np.random.seed(0)
            for extent in (np.array([20., 30., .2]), np.array([.1, .2, .3])):
                center = np.array([-8., 7., 2.])
                obj = SimpleNamespace(aabb_center=center, aabb_extent=extent)
                for _ in range(100):
                    point = sample_aabb_side(obj)
                    self.assertTrue(np.all(np.abs(point - center) <= extent / 2 + 1e-10))
                    self.assertTrue(np.any(np.isclose(np.abs(point - center)[:2], extent[:2] / 2)))
        finally:
            np.random.set_state(state)

    def test_affinity_cannot_expand_outside_available_cpus(self):
        with patch.dict(os.environ, {'VAPTAMP_CPU_AFFINITY': '16-31'}), \
             patch('os.sched_getaffinity', return_value={0, 1}), \
             patch('os.sched_setaffinity') as setter:
            with self.assertRaises(ValueError):
                apply_cpu_affinity()
            setter.assert_not_called()

    def test_affinity_only_changes_current_process(self):
        with patch.dict(os.environ, {'VAPTAMP_CPU_AFFINITY': '16-31'}), \
             patch('os.sched_getaffinity', return_value=set(range(32))), \
             patch('os.sched_setaffinity') as setter:
            apply_cpu_affinity()
            setter.assert_called_once_with(0, set(range(16, 32)))
