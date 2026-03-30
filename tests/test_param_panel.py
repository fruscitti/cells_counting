import pytest


@pytest.fixture
def param_panel(qtbot):
    from ui.param_panel import ParamPanel
    panel = ParamPanel()
    qtbot.addWidget(panel)
    panel.show()
    return panel


def test_brightness_slider(param_panel):
    """PARAM-01: Brightness slider range 0-255, default 120."""
    s = param_panel.brightness_slider
    assert s.minimum() == 0
    assert s.maximum() == 255
    assert s.value() == 120


def test_min_area_slider(param_panel):
    """PARAM-02: Min Cell Area slider range 1-500, default 25."""
    s = param_panel.min_area_slider
    assert s.minimum() == 1
    assert s.maximum() == 500
    assert s.value() == 25


def test_blur_odd_enforcement(param_panel):
    """PARAM-03: Blur spinbox enforces odd values only."""
    sb = param_panel.blur_spinbox
    assert sb.minimum() == 1
    assert sb.maximum() == 31
    assert sb.value() == 9
    sb.setValue(10)
    # After setting even value, stepBy or correction should make it odd
    # The OddSpinBox.stepBy ensures odd on step; direct setValue may need clamping in get_params
    # At minimum, get_params must return odd value
    params = param_panel.get_params()
    assert params["blur_strength"] % 2 == 1


def test_max_area(param_panel):
    """PARAM-04: Max Cell Area range 50-5000, default 500."""
    params = param_panel.get_params()
    assert params["max_cell_area"] == 500


def test_cleaning_default(param_panel):
    """PARAM-05: Use Cleaning checkbox default checked."""
    assert param_panel.cleaning_checkbox.isChecked()


def test_tophat_visibility(param_panel):
    """PARAM-06: Top-hat sub-controls hidden when unchecked, visible when checked."""
    assert not param_panel.tophat_checkbox.isChecked()
    assert not param_panel.tophat_container.isVisible()
    param_panel.tophat_checkbox.setChecked(True)
    assert param_panel.tophat_container.isVisible()


def test_value_labels(param_panel):
    """PARAM-07: Value labels update when slider changes."""
    param_panel.brightness_slider.setValue(200)
    assert param_panel.brightness_value.text() == "200"
    param_panel.adaptive_c_slider.setValue(-10)
    assert param_panel.adaptive_c_value.text() == "-10"


def test_get_params_keys(param_panel):
    """get_params returns all 9 parameter keys."""
    params = param_panel.get_params()
    expected_keys = {"brightness_threshold", "min_cell_area", "blur_strength",
                     "max_cell_area", "use_cleaning", "use_tophat",
                     "tophat_kernel", "adaptive_block", "adaptive_c"}
    assert set(params.keys()) == expected_keys


def test_set_params_partial(param_panel):
    """set_params handles partial dicts without KeyError (e.g., from auto-optimize)."""
    # Auto-optimize only returns 3 keys
    partial = {"brightness_threshold": 80, "min_cell_area": 15, "blur_strength": 7}
    param_panel.set_params(partial)
    assert param_panel.brightness_slider.value() == 80
    assert param_panel.min_area_slider.value() == 15
    assert param_panel.blur_spinbox.value() == 7
    # Other params should remain at defaults
    assert param_panel.cleaning_checkbox.isChecked()
    assert param_panel.get_params()["max_cell_area"] == 500


def test_reset_defaults(param_panel):
    """reset_defaults restores all controls to DEFAULTS."""
    param_panel.brightness_slider.setValue(50)
    param_panel.reset_defaults()
    assert param_panel.brightness_slider.value() == 120
    assert param_panel.blur_spinbox.value() == 9
