# encoding: utf-8

"""
Custom element classes related to the styles part
"""

from ..enum.style import WD_STYLE_TYPE
from .simpletypes import ST_OnOff, ST_String
from .xmlchemy import (
    BaseOxmlElement, OptionalAttribute, ZeroOrMore, ZeroOrOne
)


def styleId_from_name(name):
    """
    Return the style id corresponding to *name*, taking into account
    special-case names such as 'Heading 1'.
    """
    return {
        'caption':   'Caption',
        'heading 1': 'Heading1',
        'heading 2': 'Heading2',
        'heading 3': 'Heading3',
        'heading 4': 'Heading4',
        'heading 5': 'Heading5',
        'heading 6': 'Heading6',
        'heading 7': 'Heading7',
        'heading 8': 'Heading8',
        'heading 9': 'Heading9',
    }.get(name, name.replace(' ', ''))


class CT_Style(BaseOxmlElement):
    """
    A ``<w:style>`` element, representing a style definition
    """
    _tag_seq = (
        'w:name', 'w:aliases', 'w:basedOn', 'w:next', 'w:link',
        'w:autoRedefine', 'w:hidden', 'w:uiPriority', 'w:semiHidden',
        'w:unhideWhenUsed', 'w:qFormat', 'w:locked', 'w:personal',
        'w:personalCompose', 'w:personalReply', 'w:rsid', 'w:pPr', 'w:rPr',
        'w:tblPr', 'w:trPr', 'w:tcPr', 'w:tblStylePr'
    )
    name = ZeroOrOne('w:name', successors=_tag_seq[1:])
    basedOn = ZeroOrOne('w:basedOn', successors=_tag_seq[3:])
    uiPriority = ZeroOrOne('w:uiPriority', successors=_tag_seq[8:])
    semiHidden = ZeroOrOne('w:semiHidden', successors=_tag_seq[9:])
    pPr = ZeroOrOne('w:pPr', successors=_tag_seq[17:])
    rPr = ZeroOrOne('w:rPr', successors=_tag_seq[18:])
    del _tag_seq

    type = OptionalAttribute('w:type', WD_STYLE_TYPE)
    styleId = OptionalAttribute('w:styleId', ST_String)
    default = OptionalAttribute('w:default', ST_OnOff)
    customStyle = OptionalAttribute('w:customStyle', ST_OnOff)

    @property
    def basedOn_val(self):
        """
        Value of `w:basedOn/@w:val` or |None| if not present.
        """
        basedOn = self.basedOn
        if basedOn is None:
            return None
        return basedOn.val

    @basedOn_val.setter
    def basedOn_val(self, value):
        if value is None:
            self._remove_basedOn()
        else:
            self.get_or_add_basedOn().val = value

    @property
    def base_style(self):
        """
        Sibling CT_Style element this style is based on or |None| if no base
        style or base style not found.
        """
        basedOn = self.basedOn
        if basedOn is None:
            return None
        styles = self.getparent()
        base_style = styles.get_by_id(basedOn.val)
        if base_style is None:
            return None
        return base_style

    def delete(self):
        """
        Remove this `w:style` element from its parent `w:styles` element.
        """
        self.getparent().remove(self)

    @property
    def name_val(self):
        """
        Value of ``<w:name>`` child or |None| if not present.
        """
        name = self.name
        if name is None:
            return None
        return name.val

    @name_val.setter
    def name_val(self, value):
        self._remove_name()
        if value is not None:
            name = self._add_name()
            name.val = value

    @property
    def semiHidden_val(self):
        """
        Value of ``<w:semiHidden>`` child or |False| if not present.
        """
        semiHidden = self.semiHidden
        if semiHidden is None:
            return False
        return semiHidden.val

    @semiHidden_val.setter
    def semiHidden_val(self, value):
        self._remove_semiHidden()
        if bool(value) is True:
            semiHidden = self._add_semiHidden()
            semiHidden.val = value

    @property
    def uiPriority_val(self):
        """
        Value of ``<w:uiPriority>`` child or |None| if not present.
        """
        uiPriority = self.uiPriority
        if uiPriority is None:
            return None
        return uiPriority.val


class CT_Styles(BaseOxmlElement):
    """
    ``<w:styles>`` element, the root element of a styles part, i.e.
    styles.xml
    """
    style = ZeroOrMore('w:style', successors=())

    def add_style_of_type(self, name, style_type, builtin):
        """
        Return a newly added `w:style` element having *name* and
        *style_type*. `w:style/@customStyle` is set based on the value of
        *builtin*.
        """
        style = self.add_style()
        style.type = style_type
        style.customStyle = None if builtin else True
        style.styleId = styleId_from_name(name)
        style.name_val = name
        return style

    def default_for(self, style_type):
        """
        Return `w:style[@w:type="*{style_type}*][-1]` or |None| if not found.
        """
        default_styles_for_type = [
            s for s in self._iter_styles()
            if s.type == style_type and s.default
        ]
        if not default_styles_for_type:
            return None
        # spec calls for last default in document order
        return default_styles_for_type[-1]

    def get_by_id(self, styleId):
        """
        Return the ``<w:style>`` child element having ``styleId`` attribute
        matching *styleId*, or |None| if not found.
        """
        xpath = 'w:style[@w:styleId="%s"]' % styleId
        try:
            return self.xpath(xpath)[0]
        except IndexError:
            return None

    def get_by_name(self, name):
        """
        Return the ``<w:style>`` child element having ``<w:name>`` child
        element with value *name*, or |None| if not found.
        """
        xpath = 'w:style[w:name/@w:val="%s"]' % name
        try:
            return self.xpath(xpath)[0]
        except IndexError:
            return None

    def _iter_styles(self):
        """
        Generate each of the `w:style` child elements in document order.
        """
        return (style for style in self.xpath('w:style'))