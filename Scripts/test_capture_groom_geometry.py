"""Numerical contracts for UV reconstruction, independent of Blender."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

spec = importlib.util.spec_from_file_location('capture_groom', Path(__file__).with_name('build_capture_groom_blender.py'))
groom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(groom)


class UVReconstructionTest(unittest.TestCase):
    def test_barycentric_mapping_preserves_bent_card_and_rejects_holes(self):
        uv = np.array([[[0, 0], [1, 0], [0, 1]], [[1, 0], [1, 1], [0, 1]]], dtype=float)
        xyz = np.array([[[0, 0, 0], [2, 0, 0], [0, 0, 3]], [[2, 0, 0], [2, 1, 3], [0, 0, 3]]], dtype=float)
        points = np.array([[.25, .25], [.75, .75], [1.2, .5]])
        mapped, valid = groom.uv_to_xyz(points, uv, xyz)
        np.testing.assert_array_equal(valid, [True, True, False])
        np.testing.assert_allclose(mapped[:2], [[.5, 0, .75], [1.5, .5, 2.25]])

    def test_weighted_quantiles_follow_curved_opacity_strand(self):
        u = np.linspace(0, 1, 257)
        rows = np.linspace(0, 1, 19)
        centers = .2 + .45 * rows ** 2
        alpha = np.exp(-((u[None, :] - centers[:, None]) / .02) ** 2)
        paths = groom.weighted_u_paths(u, alpha, np.array([.5]))
        np.testing.assert_allclose(paths[:, 0], centers, atol=.006)

    def test_longest_run_does_not_bridge_transparent_gap(self):
        self.assertEqual(groom.longest_true_run(np.array([0, 1, 1, 0, 1, 1, 1, 0], bool)), (4, 7))

    def test_root_is_nearest_to_scalp(self):
        curve = np.array([[0, 0, 1], [0, 0, .5], [0, 0, .1]])
        ordered, flipped = groom.orient_root(curve, lambda p: abs(p[2]))
        self.assertTrue(flipped)
        np.testing.assert_array_equal(ordered[0], [0, 0, .1])

    def test_ue_coordinates_are_centimeters_and_reflect_y(self):
        np.testing.assert_allclose(groom.blender_m_to_ue_cm(np.array([[.2, -.3, 1.7]])), [[20, 30, 170]])


if __name__ == '__main__':
    unittest.main()
