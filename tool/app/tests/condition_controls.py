"""Exercise visible tri-state controls, never hidden boolean injection."""
def set_checked(page, selector=None, checked=True):
    if isinstance(selector, bool):
        checked=selector
        selector=None
    control=page.locator(selector) if selector is not None else page
    if control.evaluate('(e)=>e.tagName')=='SELECT':
        control.select_option('yes' if checked else 'unknown')
    else:
        control.set_checked(checked)

def is_checked(control):
    if control.evaluate('(e)=>e.tagName')=='SELECT':
        return control.input_value()=='yes'
    return control.is_checked()
