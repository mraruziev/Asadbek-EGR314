from __future__ import annotations

import numpy as np

from leaf_ai.realtime import center_square, is_healthy, parse_source, pretty_label


def test_pretty_label_splits_plant_from_disease():
    assert pretty_label("Tomato___Late_blight") == "Tomato - Late blight"
    assert pretty_label("Apple__Apple_scab") == "Apple - Apple scab"


def test_pretty_label_passes_through_unseparated_names():
    assert pretty_label("Soybean_healthy") == "Soybean healthy"


def test_is_healthy_matches_only_healthy_suffix():
    assert is_healthy("Tomato___healthy")
    assert not is_healthy("Tomato___Late_blight")


def test_parse_source_handles_index_and_path():
    assert parse_source("0") == 0
    assert parse_source("clip.mp4") == "clip.mp4"


def test_center_square_is_square_and_inside_frame():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    crop, (left, top, right, bottom) = center_square(frame, 0.8)
    assert crop.shape[0] == crop.shape[1] == 384
    assert 0 <= left < right <= 640
    assert 0 <= top < bottom <= 480


def test_vegetation_fraction_separates_foliage_from_skin_and_walls():
    from leaf_ai.realtime import vegetation_fraction

    foliage = np.full((64, 64, 3), (40, 160, 50), dtype=np.uint8)  # BGR green
    skin = np.full((64, 64, 3), (110, 150, 200), dtype=np.uint8)
    wall = np.full((64, 64, 3), (200, 200, 200), dtype=np.uint8)

    assert vegetation_fraction(foliage) > 0.9
    assert vegetation_fraction(skin) < 0.05
    assert vegetation_fraction(wall) < 0.05


def test_vegetation_fraction_handles_empty_crop():
    from leaf_ai.realtime import vegetation_fraction

    assert vegetation_fraction(np.zeros((0, 0, 3), dtype=np.uint8)) == 0.0
    assert vegetation_fraction(None) == 0.0


def test_split_label_separates_species_kind_and_disease():
    from leaf_ai.realtime import split_label

    assert split_label("Tomato_Late_blight") == ("Tomato", "vegetable", "Late blight")
    assert split_label("Apple_healthy") == ("Apple", "fruit", "")
    assert split_label("Corn_maize_Common_rust") == ("Corn (maize)", "grain", "Common rust")


def test_split_label_prefers_the_longer_species_prefix():
    from leaf_ai.realtime import split_label

    species, kind, _ = split_label("Cherry_including_sour_Powdery_mildew")
    assert (species, kind) == ("Cherry", "fruit")


def test_describe_names_the_produce_when_healthy():
    from leaf_ai.realtime import describe

    assert describe("Tomato_healthy") == "Healthy Tomato - vegetable"
    assert describe("Blueberry_healthy") == "Healthy Blueberry - fruit"
    assert describe("Soybean_healthy") == "Healthy Soybean - legume"


def test_describe_names_the_disease_when_present():
    from leaf_ai.realtime import describe

    assert describe("Potato_Early_blight") == "Potato: Early blight"


def test_describe_handles_upstream_triple_underscore_names():
    from leaf_ai.realtime import describe

    assert describe("Tomato___healthy") == "Healthy Tomato - vegetable"


def test_reject_class_is_never_a_plant():
    from leaf_ai.realtime import describe, is_healthy, is_reject

    assert is_reject("Not_a_leaf")
    assert not is_healthy("Not_a_leaf")
    assert describe("Not_a_leaf") == "not a leaf"


def test_is_finished_rejects_a_run_that_stopped_early(tmp_path):
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
    from webcam import is_finished

    run = tmp_path / "run"
    run.mkdir()
    (run / "args.yaml").write_text("epochs: 8\nimgsz: 224\n")
    (run / "results.csv").write_text("epoch,time\n1,10\n2,20\n")
    assert not is_finished(run)

    (run / "results.csv").write_text("epoch,time\n" + "".join(f"{i},10\n" for i in range(1, 9)))
    assert is_finished(run)


def test_is_finished_rejects_a_run_with_no_results(tmp_path):
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
    from webcam import is_finished

    run = tmp_path / "empty"
    run.mkdir()
    assert not is_finished(run)
