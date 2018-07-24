import bpy, struct, bmesh, numpy
import os

from math import *
from mathutils import *

from random import random

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

class BFRESslot():
    data = None
    
flipYZ = Matrix(((1,0,0,0), (0,0,-1,0), (0,1,0,0), (0,0,0,1)))

class LoD():
    def __init__(self, offset, parent, bfres):
        self.offset = offset
        self.parent = parent
        self.bfres = bfres
    def primitive_type(self):
        return struct.unpack(">I", self.bfres.bytes[self.offset:self.offset+0x4])[0]
    def index_format(self):
        return struct.unpack(">I", self.bfres.bytes[self.offset+0x4:self.offset+0x8])[0]
    def count_of_points(self):
        return struct.unpack(">I", self.bfres.bytes[self.offset+0x8:self.offset+0xC])[0]
    def index_buffer_offset(self):
        return self.offset+0x14+struct.unpack(">i", self.bfres.bytes[self.offset+0x14:self.offset+0x18])[0]
    
    def primitive_type_string(self):
        pt = self.primitive_type()
        if pt == 0x01: return "GX2_PRIMITIVE_POINTS"                        #< min = 1; incr = 1
        elif pt == 0x02: return "GX2_PRIMITIVE_LINES"                       #< min = 2; incr = 2
        elif pt == 0x03: return "GX2_PRIMITIVE_LINE_STRIP"                  #< min = 2; incr = 1
        elif pt == 0x04: return "GX2_PRIMITIVE_TRIANGLES"                   #< min = 3; incr = 3
        elif pt == 0x05: return "GX2_PRIMITIVE_TRIANGLE_FAN"                #< min = 3; incr = 1
        elif pt == 0x06: return "GX2_PRIMITIVE_TRIANGLE_STRIP"              #< min = 3; incr = 1
        elif pt == 0x0a: return "GX2_PRIMITIVE_LINES_ADJACENCY"             #< min = 4; incr = 4
        elif pt == 0x0b: return "GX2_PRIMITIVE_LINE_STRIP_ADJACENCY"        #< min = 4; incr = 1
        elif pt == 0x0c: return "GX2_PRIMITIVE_TRIANGLES_ADJACENCY"         #< min = 6; incr = 6
        elif pt == 0x0d: return "GX2_PRIMITIVE_TRIANGLE_STRIP_ADJACENCY"    #< min = 6; incr = 2
        elif pt == 0x11: return "GX2_PRIMITIVE_RECTS"                       #< min = 3; incr = 3
        elif pt == 0x12: return "GX2_PRIMITIVE_LINE_LOOP"                   #< min = 2; incr = 1
        elif pt == 0x13: return "GX2_PRIMITIVE_QUADS"                       #< min = 4; incr = 4
        elif pt == 0x14: return "GX2_PRIMITIVE_QUAD_STRIP"                  #< min = 4; incr = 2
        elif pt == 0x82: return "GX2_PRIMITIVE_TESSELLATE_LINES"            #< min = 2; incr = 2
        elif pt == 0x83: return "GX2_PRIMITIVE_TESSELLATE_LINE_STRIP"       #< min = 2; incr = 1
        elif pt == 0x84: return "GX2_PRIMITIVE_TESSELLATE_TRIANGLES"        #< min = 3; incr = 3
        elif pt == 0x86: return "GX2_PRIMITIVE_TESSELLATE_TRIANGLE_STRIP"   #< min = 3; incr = 1
        elif pt == 0x93: return "GX2_PRIMITIVE_TESSELLATE_QUADS"            #< min = 4; incr = 4
        elif pt == 0x94: return "GX2_PRIMITIVE_TESSELLATE_QUAD_STRIP"       #< min = 4; incr = 2
        else: return "unknown"
    
    def index_format_string(self):
        i_f = self.index_format()
        if i_f == 0: return "GX2_INDEX_FORMAT_U16_LE"
        elif i_f == 1: return "GX2_INDEX_FORMAT_U32_LE"
        elif i_f == 4: return "GX2_INDEX_FORMAT_U16"
        elif i_f == 9: return "GX2_INDEX_FORMAT_U32"
        else: return "unknown"
    
    def get_buffer_offset(self):
        offset = self.index_buffer_offset()
        return offset+0x14+struct.unpack(">i", self.bfres.bytes[offset+0x14:offset+0x18])[0]
    
    def get_buffer_size(self):
        offset = self.index_buffer_offset()
        return struct.unpack(">i", self.bfres.bytes[offset+0x4:offset+0x8])[0]

class vtxAttribute():
    def __init__(self, offset, parent, bfres):
        self.offset = offset
        self.parent = parent
        self.bfres = bfres
    def buffer_index(self):
        return self.bfres.bytes[self.offset+4]
    def format(self):
        return struct.unpack(">I", self.bfres.bytes[self.offset+8:self.offset+0xC])[0]
    def format_string(self):
        fmt = self.format()
        if fmt == 0x0000:    return "unorm_8"
        elif fmt == 0x0004:    return "unorm_8_8"
        elif fmt == 0x0007:    return "unorm_16_16"
        elif fmt == 0x000A:    return "unorm_8_8_8_8"
        elif fmt == 0x0100:    return "uint_8"
        elif fmt == 0x0104:    return "uint_8_8"
        elif fmt == 0x010A:    return "uint_8_8_8_8"
        elif fmt == 0x0200:    return "snorm_8"
        elif fmt == 0x0204:    return "snorm_8_8"
        elif fmt == 0x0207:    return "snorm_16_16"
        elif fmt == 0x020A:    return "snorm_8_8_8_8"
        elif fmt == 0x020B:    return "snorm_10_10_10_2"
        elif fmt == 0x0300:    return "sint_8"
        elif fmt == 0x0304:    return "sint_8_8"
        elif fmt == 0x030A:    return "sint_8_8_8_8"
        elif fmt == 0x0806:    return "float_32"
        elif fmt == 0x0808:    return "float_16_16"
        elif fmt == 0x080D:    return "float_32_32"
        elif fmt == 0x080F:    return "float_16_16_16_16"
        elif fmt == 0x0811:    return "float_32_32_32"
        elif fmt == 0x0813:    return "float_32_32_32_32"
        else: return "unknown"
    def buffer_offset(self):
        return struct.unpack(">h", self.bfres.bytes[self.offset+0x6:self.offset+0x8])[0]

class FVTX():
    def __init__(self, offset, parent, bfres):
        self.offset = offset
        self.parent = parent
        self.bfres = bfres
    def magic(self):
        return self.bfres.bytes[self.offset:self.offset+4]
    def attribute_count(self):
        return self.bfres.bytes[self.offset+4]
    def buffer_count(self):
        return self.bfres.bytes[self.offset+5]
    def section_index(self):
        return struct.unpack(">H", self.bfres.bytes[self.offset+6:self.offset+8])[0]
    def num_vertices(self):
        return struct.unpack(">I", self.bfres.bytes[self.offset+8:self.offset+0xC])[0]
    def vertex_skin_count(self):
        return self.bfres.bytes[self.offset+0xC]
    def attribute_array_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x10:self.offset+0x14])[0]+0x10
    def attribute_index_group_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x14:self.offset+0x18])[0]+0x14
    def buffer_array_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x18:self.offset+0x1C])[0]+0x18
    
    def get_attribute_name(self, i):
        offset = self.attribute_index_group_offset()
        name_pointer_offset = offset+0x20+i*0x10
        name_offset = name_pointer_offset+struct.unpack(">i", self.bfres.bytes[name_pointer_offset:name_pointer_offset+4])[0]
        size_of_name = struct.unpack(">i", self.bfres.bytes[name_offset-4:name_offset])[0]
        return self.bfres.bytes[name_offset:name_offset+size_of_name].decode("UTF-8")
    
    def get_attribute_data(self, i):
        offset = self.attribute_index_group_offset()
        pointer_offset = offset+0x24+i*0x10
        offset = pointer_offset+struct.unpack(">i", self.bfres.bytes[pointer_offset:pointer_offset+4])[0]
        return vtxAttribute(offset, self, self.bfres)
    
    def get_buffer_offset(self, i):
        offset = self.buffer_array_offset()
        return offset+i*0x18+struct.unpack(">i", self.bfres.bytes[offset+i*0x18+0x14:offset+i*0x18+0x18])[0]+0x14
    
    def get_buffer_size(self, i):
        offset = self.buffer_array_offset()
        return struct.unpack(">I", self.bfres.bytes[offset+i*0x18+0x4:offset+i*0x18+0x8])[0]
    
    def get_buffer_stride(self, i):
        offset = self.buffer_array_offset()
        return struct.unpack(">H", self.bfres.bytes[offset+i*0x18+0xC:offset+i*0x18+0xE])[0]
    
class FSHP():
    def __init__(self, offset, parent, bfres):
        self.offset = offset
        self.parent = parent
        self.bfres = bfres
    def magic(self):
        return self.bfres.bytes[self.offset:self.offset+4]
    def section_index(self):
        return struct.unpack(">H", self.bfres.bytes[self.offset+0xC:self.offset+0xE])[0]
    def material_index(self):
        return struct.unpack(">H", self.bfres.bytes[self.offset+0xE:self.offset+0x10])[0]
    def skeleton_index(self):
        return struct.unpack(">H", self.bfres.bytes[self.offset+0x10:self.offset+0x12])[0]
    def vertex_index(self):
        return struct.unpack(">H", self.bfres.bytes[self.offset+0x12:self.offset+0x14])[0]
    def skeleton_bone_skin_index(self):
        return struct.unpack(">H", self.bfres.bytes[self.offset+0x14:self.offset+0x16])[0]
    def vertex_skin_count(self):
        return self.bfres.bytes[self.offset+0x16]
    def LoD_model_count(self):
        return self.bfres.bytes[self.offset+0x17]
    def key_shape_count(self):
        return self.bfres.bytes[self.offset+0x18]
    def vertex_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x20:self.offset+0x24])[0]+0x20
    def LoD_model_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x24:self.offset+0x28])[0]+0x24
    def skeleton_index_array_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x28:self.offset+0x2C])[0]+0x28

    def get_LoD_model(self, i):
        return LoD(self.LoD_model_offset(), self, self.bfres)
    
    def get_bone_index(self, i):
        offset = self.skeleton_index_array_offset()
        return struct.unpack(">H", self.bfres.bytes[offset+2*i:offset+2*i+2])[0]
class texSampParam():
    def __init__(self, offset, parent, bfres):
        self.offset = offset
        self.parent = parent
        self.bfres = bfres 
    def index(self):
        return self.bfres.bytes[self.offset+0x14]
    
        
class matParam():
    def __init__(self, offset, parent, bfres):
        self.offset = offset
        self.parent = parent
        self.bfres = bfres
    def type(self):
        return self.bfres.bytes[self.offset]
    def type_string(self):
        t = self.type()
        return  "1 bool"                    if type == 0 else\
                "2 bool"                    if type == 1 else\
                "3 bool"                    if type == 2 else\
                "4 bool"                    if type == 3 else\
                "1 signed int"              if type == 4 else\
                "2 signed int"              if type == 5 else\
                "3 signed int"              if type == 6 else\
                "4 signed int"              if type == 7 else\
                "1 unsigned int"            if type == 8 else\
                "2 unsigned int"            if type == 9 else\
                "3 unsigned int"            if type == 10 else\
                "4 unsigned int"            if type == 11 else\
                "1 float"                   if type == 12 else\
                "2 float"                   if type == 13 else\
                "3 float"                   if type == 14 else\
                "4 float"                   if type == 15 else\
                "2x2 Matrix"                if type == 16 else\
                "2x3 Matrix"                if type == 17 else\
                "2x4 Matrix"                if type == 18 else\
                "3x2 Matrix"                if type == 19 else\
                "3x3 Matrix"                if type == 20 else\
                "3x4 Matrix"                if type == 21 else\
                "4x2 Matrix"                if type == 22 else\
                "4x3 Matrix"                if type == 23 else\
                "4x4 Matrix"                if type == 24 else\
                "2D SRT"                    if type == 25 else\
                "3D SRT"                    if type == 26 else\
                "Texture SRT"               if type == 27 else\
                "Texture SRT * 3x4 Matrix"  if type == 28 else\
                "<unknown: %i>" % t
    def value_offset(self):
        return self.offset+struct.unpack(">h", self.bfres.bytes[self.offset:self.offset+2])[0]
    def value(self):
        offset = self.value_offset()
        return None

class FMAT():
    def __init__(self, offset, parent, bfres):
        self.offset = offset
        self.parent = parent
        self.bfres = bfres
    def magic(self):
        return self.bfres.bytes[self.offset:self.offset+4]
    
    def texture_reference_count(self):return self.bfres.bytes[self.offset+0x10]
    
    def texture_param_count(self):return self.bfres.bytes[self.offset+0x11]

    def material_param_count(self):return self.bfres.bytes[self.offset+0x12]|(self.bfres.bytes[self.offset+0x13]<<8)
    
    def section_index(self):
        return struct.unpack(">H", self.bfres.bytes[self.offset+0xC:self.offset+0xE])[0]
    
    def texture_param_array_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x30:self.offset+0x34])[0]+0x30

    def get_texture_param_data(self, i):
        for j in range(self.texture_param_count()):
            offset = self.texture_param_array_offset()
            pointer_offset = offset+0x24+j*0x10
            offset = pointer_offset+struct.unpack(">i", self.bfres.bytes[pointer_offset:pointer_offset+4])[0]
            bn = texSampParam(offset, self, self.bfres)
            if bn.index() == i:
                return bn
    
    def get_texture_param_name(self, i):
        for j in range(self.texture_param_count()):
            offset = self.texture_param_array_offset()
            pointer_offset = offset+0x24+j*0x10
            offset = pointer_offset+struct.unpack(">i", self.bfres.bytes[pointer_offset:pointer_offset+4])[0]
            bn = texSampParam(offset, self, self.bfres)
            if bn.index() == i:
                offset = self.texture_param_array_offset()
                name_pointer_offset = offset+0x20+j*0x10
                name_offset = name_pointer_offset+struct.unpack(">i", self.bfres.bytes[name_pointer_offset:name_pointer_offset+4])[0]
                size_of_name = struct.unpack(">i", self.bfres.bytes[name_offset-4:name_offset])[0]
                return self.bfres.bytes[name_offset:name_offset+size_of_name].decode("UTF-8")
          
    def material_param_array_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x38:self.offset+0x3C])[0]+0x38

    def get_material_param_data(self, i):
        for j in range(self.material_param_count()):
            offset = self.material_param_array_offset()
            pointer_offset = offset+0x24+j*0x10
            offset = pointer_offset+struct.unpack(">i", self.bfres.bytes[pointer_offset:pointer_offset+4])[0]
            bn = matParam(offset, self, self.bfres)
            if bn.index() == i:
                return bn
    
    def get_material_param_name(self, i):
        for j in range(self.material_param_count()):
            offset = self.material_param_array_offset()
            pointer_offset = offset+0x24+j*0x10
            offset = pointer_offset+struct.unpack(">i", self.bfres.bytes[pointer_offset:pointer_offset+4])[0]
            bn = matParam(offset, self, self.bfres)
            if bn.index() == i:
                offset = self.texture_param_array_offset()
                name_pointer_offset = offset+0x20+j*0x10
                name_offset = name_pointer_offset+struct.unpack(">i", self.bfres.bytes[name_pointer_offset:name_pointer_offset+4])[0]
                size_of_name = struct.unpack(">i", self.bfres.bytes[name_offset-4:name_offset])[0]
                return self.bfres.bytes[name_offset:name_offset+size_of_name].decode("UTF-8")
    def material_param_data_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x3C:self.offset+0x40])[0]+0x3C
    
    def get_texture_offset(self, i):
        offset = self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x28:self.offset+0x2C])[0]+0x28+i*8
        return offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x4:self.offset+0x8])[0]+4
    def get_texture_name(self, i):
        offset = self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x28:self.offset+0x2C])[0]+0x28+i*8
        name_offset = offset+struct.unpack(">i", self.bfres.bytes[offset:offset+0x4])[0]
        size_of_name = struct.unpack(">i", self.bfres.bytes[name_offset-4:name_offset])[0]
        return self.bfres.bytes[name_offset:name_offset+size_of_name].decode("UTF-8")
    
class bone():
    def __init__(self, offset, parent, bfres):
        self.offset = offset
        self.parent = parent
        self.bfres = bfres
    def index(self):
        return struct.unpack(">h", self.bfres.bytes[self.offset+0x4:self.offset+0x6])[0]
    def parent_index(self):
        return struct.unpack(">h", self.bfres.bytes[self.offset+0x6:self.offset+0x8])[0]
    def smooth_matrix_index(self):
        return struct.unpack(">h", self.bfres.bytes[self.offset+0x8:self.offset+0xA])[0]
    def rigid_matrix_index(self):
        return struct.unpack(">h", self.bfres.bytes[self.offset+0xA:self.offset+0xC])[0]
    def billboard_index(self):
        return struct.unpack(">h", self.bfres.bytes[self.offset+0xC:self.offset+0xE])[0]
    def uses_euler(self):
        return (struct.unpack(">I", self.bfres.bytes[self.offset+0x10:self.offset+0x14])[0]&0b00000000000000000001000000000000) != 0
    def scale_vector(self):
        return struct.unpack(">3f", self.bfres.bytes[self.offset+0x14:self.offset+0x20])
    def rotation_vector(self):
        return struct.unpack(">4f", self.bfres.bytes[self.offset+0x20:self.offset+0x30])
    def translation_vector(self):
        return struct.unpack(">3f", self.bfres.bytes[self.offset+0x30:self.offset+0x3C])

class FSKL():
    def __init__(self, offset, parent, bfres):
        self.offset = offset
        self.parent = parent
        self.bfres = bfres
    def magic(self):
        return self.bfres.bytes[self.offset:self.offset+4]
    def num_bones(self):
        return struct.unpack(">H", self.bfres.bytes[self.offset+0x8:self.offset+0xA])[0]
    def num_smooth_indexes(self):
        return struct.unpack(">H", self.bfres.bytes[self.offset+0xA:self.offset+0xC])[0]
    def num_rigid_indexes(self):
        return struct.unpack(">H", self.bfres.bytes[self.offset+0xC:self.offset+0xE])[0]
    def bone_index_group_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x10:self.offset+0x14])[0]+0x10
    def bone_array_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x14:self.offset+0x18])[0]+0x14
    def smooth_index_array_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x18:self.offset+0x1C])[0]+0x18
    def smooth_matrix_array_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x1C:self.offset+0x20])[0]+0x1C
    
    def get_bone_data(self, i, listorder = False):
        if listorder:
            offset = self.bone_index_group_offset()
            pointer_offset = offset+0x24+i*0x10
            offset = pointer_offset+struct.unpack(">i", self.bfres.bytes[pointer_offset:pointer_offset+4])[0]
            return bone(offset, self, self.bfres)
        else:
            for j in range(self.num_bones()):
                offset = self.bone_index_group_offset()
                pointer_offset = offset+0x24+j*0x10
                offset = pointer_offset+struct.unpack(">i", self.bfres.bytes[pointer_offset:pointer_offset+4])[0]
                bn = bone(offset, self, self.bfres)
                if bn.index() == i:
                    return bn
    
    def get_bone_name(self, i, listorder = False):
        if listorder:
            offset = self.bone_index_group_offset()
            name_pointer_offset = offset+0x20+i*0x10
            name_offset = name_pointer_offset+struct.unpack(">i", self.bfres.bytes[name_pointer_offset:name_pointer_offset+4])[0]
            size_of_name = struct.unpack(">i", self.bfres.bytes[name_offset-4:name_offset])[0]
            return self.bfres.bytes[name_offset:name_offset+size_of_name].decode("UTF-8")
        else:
            for j in range(self.num_bones()):
                offset = self.bone_index_group_offset()
                pointer_offset = offset+0x24+j*0x10
                offset = pointer_offset+struct.unpack(">i", self.bfres.bytes[pointer_offset:pointer_offset+4])[0]
                bn = bone(offset, self, self.bfres)
                if bn.index() == i:
                    offset = self.bone_index_group_offset()
                    name_pointer_offset = offset+0x20+j*0x10
                    name_offset = name_pointer_offset+struct.unpack(">i", self.bfres.bytes[name_pointer_offset:name_pointer_offset+4])[0]
                    size_of_name = struct.unpack(">i", self.bfres.bytes[name_offset-4:name_offset])[0]
                    return self.bfres.bytes[name_offset:name_offset+size_of_name].decode("UTF-8")
            
    def get_smooth_matrix(self, i):
        offset = self.smooth_matrix_array_offset()+0x30*i
        return Matrix((struct.unpack(">4f", self.bfres.bytes[offset:offset+0x10]),(struct.unpack(">4f", self.bfres.bytes[offset+0x10:offset+0x20])),(struct.unpack(">4f", self.bfres.bytes[offset+0x20:offset+0x30])),(0,0,0,1)))
    def get_smooth_index(self, i):
        offset = self.smooth_index_array_offset()
        return struct.unpack(">H", self.bfres.bytes[offset+2*i:offset+2*i+2])[0]

class FMDL():
    def __init__(self, offset, bfres):
        self.offset = offset
        self.bfres = bfres
    def magic(self):
        return self.bfres.bytes[self.offset:self.offset+4]
    def skeleton_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0xC:self.offset+0x10])[0]+0xC
    def vertex_array_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x10:self.offset+0x14])[0]+0x10
    def poly_index_group_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x14:self.offset+0x18])[0]+0x14
    def mat_index_group_offset(self):
        return self.offset+struct.unpack(">i", self.bfres.bytes[self.offset+0x18:self.offset+0x1C])[0]+0x18
    def total_num_vertices(self):
        return struct.unpack(">i", self.bfres.bytes[self.offset+0x28:self.offset+0x2C])[0]
    
    def get_vertex_array(self):
        return FVTX(self.vertex_array_offset(), self, self.bfres)
    
    def get_polygon_count(self):
        offset = self.poly_index_group_offset()
        return struct.unpack(">I", self.bfres.bytes[offset+4:offset+8])[0]

    def get_material_count(self):
        offset = self.mat_index_group_offset()
        return struct.unpack(">I", self.bfres.bytes[offset+4:offset+8])[0]

    def get_polygon_name(self, i):
        offset = self.poly_index_group_offset()
        name_pointer_offset = offset+0x20+i*0x10
        name_offset = name_pointer_offset+struct.unpack(">i", self.bfres.bytes[name_pointer_offset:name_pointer_offset+4])[0]
        size_of_name = struct.unpack(">i", self.bfres.bytes[name_offset-4:name_offset])[0]
        return self.bfres.bytes[name_offset:name_offset+size_of_name].decode("UTF-8")

    def get_polygon_data(self, i):
        offset = self.poly_index_group_offset()
        pointer_offset = offset+0x24+i*0x10
        offset = pointer_offset+struct.unpack(">i", self.bfres.bytes[pointer_offset:pointer_offset+4])[0]
        return FSHP(offset, self, self.bfres)
    
    def get_material_name(self, i):
        offset = self.mat_index_group_offset()
        name_pointer_offset = offset+0x20+i*0x10
        name_offset = name_pointer_offset+struct.unpack(">i", self.bfres.bytes[name_pointer_offset:name_pointer_offset+4])[0]
        size_of_name = struct.unpack(">i", self.bfres.bytes[name_offset-4:name_offset])[0]
        return self.bfres.bytes[name_offset:name_offset+size_of_name].decode("UTF-8")

    def get_material_data(self, i):
        offset = self.mat_index_group_offset()
        pointer_offset = offset+0x24+i*0x10
        offset = pointer_offset+struct.unpack(">i", self.bfres.bytes[pointer_offset:pointer_offset+4])[0]
        return FMAT(offset, self, self.bfres)
    
    def get_skeleton_data(self):
        return FSKL(self.skeleton_offset(), self, self.bfres)
        
   

class FTEX():
    def __init__(self, offset, bfres):
        self.offset = offset
        self.bfres = bfres
    def magic(self):
        return self.bfres.bytes[self.offset:self.offset+4]
    def surface_dimension(self):return struct.unpack(">I", self.bfres.bytes[self.offset+4:self.offset+8])[0]
    def surface_dimension_string(self):
        sd = struct.unpack(">I", self.bfres.bytes[self.offset:self.offset+4])[0]
        return  "GX2_SURFACE_DIM_1D"            if sd == 0x000 else \
                "GX2_SURFACE_DIM_2D"            if sd == 0x001 else \
                "GX2_SURFACE_DIM_3D"            if sd == 0x002 else \
                "GX2_SURFACE_DIM_CUBE"          if sd == 0x003 else \
                "GX2_SURFACE_DIM_1D_ARRAY"      if sd == 0x004 else \
                "GX2_SURFACE_DIM_2D_ARRAY"      if sd == 0x005 else \
                "GX2_SURFACE_DIM_2D_MSAA"       if sd == 0x006 else \
                "GX2_SURFACE_DIM_2D_MSAA_ARRAY" if sd == 0x007 else "unknown"
    def width(self):return struct.unpack(">I", self.bfres.bytes[self.offset+8:self.offset+0xC])[0]
    def height(self):return struct.unpack(">I", self.bfres.bytes[self.offset+0xC:self.offset+0x10])[0]
    def depth(self):return struct.unpack(">I", self.bfres.bytes[self.offset+0x10:self.offset+0x14])[0]

    def num_bitmaps(self):return struct.unpack(">I", self.bfres.bytes[self.offset+0x14:self.offset+0x18])[0]

    def format(self):return struct.unpack(">I", self.bfres.bytes[self.offset+0x18:self.offset+0x1C])[0]

    def format_string(self):
        fmt = self.format()
        return "GX2_SURFACE_FORMAT_INVALID"           if fmt == 0x00000000 else \
        "GX2_SURFACE_FORMAT_TC_R8_UNORM"              if fmt == 0x00000001 else \
        "GX2_SURFACE_FORMAT_TC_R8_UINT"               if fmt == 0x00000101 else \
        "GX2_SURFACE_FORMAT_TC_R8_SNORM"              if fmt == 0x00000201 else \
        "GX2_SURFACE_FORMAT_TC_R8_SINT"               if fmt == 0x00000301 else \
        "GX2_SURFACE_FORMAT_T_R4_G4_UNORM"            if fmt == 0x00000002 else \
        "GX2_SURFACE_FORMAT_TCD_R16_UNORM"            if fmt == 0x00000005 else \
        "GX2_SURFACE_FORMAT_TC_R16_UINT"              if fmt == 0x00000105 else \
        "GX2_SURFACE_FORMAT_TC_R16_SNORM"             if fmt == 0x00000205 else \
        "GX2_SURFACE_FORMAT_TC_R16_SINT"              if fmt == 0x00000305 else \
        "GX2_SURFACE_FORMAT_TC_R16_FLOAT"             if fmt == 0x00000806 else \
        "GX2_SURFACE_FORMAT_TC_R8_G8_UNORM"           if fmt == 0x00000007 else \
        "GX2_SURFACE_FORMAT_TC_R8_G8_UINT"            if fmt == 0x00000107 else \
        "GX2_SURFACE_FORMAT_TC_R8_G8_SNORM"           if fmt == 0x00000207 else \
        "GX2_SURFACE_FORMAT_TC_R8_G8_SINT"            if fmt == 0x00000307 else \
        "GX2_SURFACE_FORMAT_TCS_R5_G6_B5_UNORM"       if fmt == 0x00000008 else \
        "GX2_SURFACE_FORMAT_TC_R5_G5_B5_A1_UNORM"     if fmt == 0x0000000a else \
        "GX2_SURFACE_FORMAT_TC_R4_G4_B4_A4_UNORM"     if fmt == 0x0000000b else \
        "GX2_SURFACE_FORMAT_TC_A1_B5_G5_R5_UNORM"     if fmt == 0x0000000c else \
        "GX2_SURFACE_FORMAT_TC_R32_UINT"              if fmt == 0x0000010d else \
        "GX2_SURFACE_FORMAT_TC_R32_SINT"              if fmt == 0x0000030d else \
        "GX2_SURFACE_FORMAT_TCD_R32_FLOAT"            if fmt == 0x0000080e else \
        "GX2_SURFACE_FORMAT_TC_R16_G16_UNORM"         if fmt == 0x0000000f else \
        "GX2_SURFACE_FORMAT_TC_R16_G16_UINT"          if fmt == 0x0000010f else \
        "GX2_SURFACE_FORMAT_TC_R16_G16_SNORM"         if fmt == 0x0000020f else \
        "GX2_SURFACE_FORMAT_TC_R16_G16_SINT"          if fmt == 0x0000030f else \
        "GX2_SURFACE_FORMAT_TC_R16_G16_FLOAT"         if fmt == 0x00000810 else \
        "GX2_SURFACE_FORMAT_D_D24_S8_UNORM"           if fmt == 0x00000011 else \
        "GX2_SURFACE_FORMAT_T_R24_UNORM_X8"           if fmt == 0x00000011 else \
        "GX2_SURFACE_FORMAT_T_X24_G8_UINT"            if fmt == 0x00000111 else \
        "GX2_SURFACE_FORMAT_D_D24_S8_FLOAT"           if fmt == 0x00000811 else \
        "GX2_SURFACE_FORMAT_TC_R11_G11_B10_FLOAT"     if fmt == 0x00000816 else \
        "GX2_SURFACE_FORMAT_TCS_R10_G10_B10_A2_UNORM" if fmt == 0x00000019 else \
        "GX2_SURFACE_FORMAT_TC_R10_G10_B10_A2_UINT"   if fmt == 0x00000119 else \
        "GX2_SURFACE_FORMAT_TC_R10_G10_B10_A2_SNORM"  if fmt == 0x00000219 else \
        "GX2_SURFACE_FORMAT_TC_R10_G10_B10_A2_SINT"   if fmt == 0x00000319 else \
        "GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_UNORM"    if fmt == 0x0000001a else \
        "GX2_SURFACE_FORMAT_TC_R8_G8_B8_A8_UINT"      if fmt == 0x0000011a else \
        "GX2_SURFACE_FORMAT_TC_R8_G8_B8_A8_SNORM"     if fmt == 0x0000021a else \
        "GX2_SURFACE_FORMAT_TC_R8_G8_B8_A8_SINT"      if fmt == 0x0000031a else \
        "GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_SRGB"     if fmt == 0x0000041a else \
        "GX2_SURFACE_FORMAT_TCS_A2_B10_G10_R10_UNORM" if fmt == 0x0000001b else \
        "GX2_SURFACE_FORMAT_TC_A2_B10_G10_R10_UINT"   if fmt == 0x0000011b else \
        "GX2_SURFACE_FORMAT_D_D32_FLOAT_S8_UINT_X24"  if fmt == 0x0000081c else \
        "GX2_SURFACE_FORMAT_T_R32_FLOAT_X8_X24"       if fmt == 0x0000081c else \
        "GX2_SURFACE_FORMAT_T_X32_G8_UINT_X24"        if fmt == 0x0000011c else \
        "GX2_SURFACE_FORMAT_TC_R32_G32_UINT"          if fmt == 0x0000011d else \
        "GX2_SURFACE_FORMAT_TC_R32_G32_SINT"          if fmt == 0x0000031d else \
        "GX2_SURFACE_FORMAT_TC_R32_G32_FLOAT"         if fmt == 0x0000081e else \
        "GX2_SURFACE_FORMAT_TC_R16_G16_B16_A16_UNORM" if fmt == 0x0000001f else \
        "GX2_SURFACE_FORMAT_TC_R16_G16_B16_A16_UINT"  if fmt == 0x0000011f else \
        "GX2_SURFACE_FORMAT_TC_R16_G16_B16_A16_SNORM" if fmt == 0x0000021f else \
        "GX2_SURFACE_FORMAT_TC_R16_G16_B16_A16_SINT"  if fmt == 0x0000031f else \
        "GX2_SURFACE_FORMAT_TC_R16_G16_B16_A16_FLOAT" if fmt == 0x00000820 else \
        "GX2_SURFACE_FORMAT_TC_R32_G32_B32_A32_UINT"  if fmt == 0x00000122 else \
        "GX2_SURFACE_FORMAT_TC_R32_G32_B32_A32_SINT"  if fmt == 0x00000322 else \
        "GX2_SURFACE_FORMAT_TC_R32_G32_B32_A32_FLOAT" if fmt == 0x00000823 else \
        "GX2_SURFACE_FORMAT_T_BC1_UNORM"              if fmt == 0x00000031 else \
        "GX2_SURFACE_FORMAT_T_BC1_SRGB"               if fmt == 0x00000431 else \
        "GX2_SURFACE_FORMAT_T_BC2_UNORM"              if fmt == 0x00000032 else \
        "GX2_SURFACE_FORMAT_T_BC2_SRGB"               if fmt == 0x00000432 else \
        "GX2_SURFACE_FORMAT_T_BC3_UNORM"              if fmt == 0x00000033 else \
        "GX2_SURFACE_FORMAT_T_BC3_SRGB"               if fmt == 0x00000433 else \
        "GX2_SURFACE_FORMAT_T_BC4_UNORM"              if fmt == 0x00000034 else \
        "GX2_SURFACE_FORMAT_T_BC4_SNORM"              if fmt == 0x00000234 else \
        "GX2_SURFACE_FORMAT_T_BC5_UNORM"              if fmt == 0x00000035 else \
        "GX2_SURFACE_FORMAT_T_BC5_SNORM"              if fmt == 0x00000235 else \
        "GX2_SURFACE_FORMAT_T_NV12_UNORM"             if fmt == 0x00000081 else \
        "GX2_SURFACE_FORMAT_LAST"                     if fmt == 0x0000083f else "unknown"
    def aa(self):return struct.unpack(">I", self.bfres.bytes[self.offset+0x1C:self.offset+0x20])[0]
    
    def data_length(self):return struct.unpack(">I", self.bfres.bytes[self.offset+0x24:self.offset+0x28])[0]

    def mipmap_data_length(self):return struct.unpack(">I", self.bfres.bytes[self.offset+0x2C:self.offset+0x30])[0]

    def tile_mode(self):return struct.unpack(">I", self.bfres.bytes[self.offset+0x34:self.offset+0x38])[0]
    def tile_mode_string(self):
        tm = self.tile_mode()
        return    "GX2_TILE_MODE_DEFAULT"     if tm == 0x00000000 else \
        "GX2_TILE_MODE_LINEAR_SPECIAL"        if tm == 0x00000010 else \
        "GX2_TILE_MODE_LINEAR_ALIGNED"        if tm == 0x00000001 else \
        "GX2_TILE_MODE_1D_TILED_THIN1"        if tm == 0x00000002 else \
        "GX2_TILE_MODE_1D_TILED_THICK"        if tm == 0x00000003 else \
        "GX2_TILE_MODE_2D_TILED_THIN1"        if tm == 0x00000004 else \
        "GX2_TILE_MODE_2D_TILED_THIN2"        if tm == 0x00000005 else \
        "GX2_TILE_MODE_2D_TILED_THIN4"        if tm == 0x00000006 else \
        "GX2_TILE_MODE_2D_TILED_THICK"        if tm == 0x00000007 else \
        "GX2_TILE_MODE_2B_TILED_THIN1"        if tm == 0x00000008 else \
        "GX2_TILE_MODE_2B_TILED_THIN2"        if tm == 0x00000009 else \
        "GX2_TILE_MODE_2B_TILED_THIN4"        if tm == 0x0000000a else \
        "GX2_TILE_MODE_2B_TILED_THICK"        if tm == 0x0000000b else \
        "GX2_TILE_MODE_3D_TILED_THIN1"        if tm == 0x0000000c else \
        "GX2_TILE_MODE_3D_TILED_THICK"        if tm == 0x0000000d else \
        "GX2_TILE_MODE_3B_TILED_THIN1"        if tm == 0x0000000e else \
        "GX2_TILE_MODE_3B_TILED_THICK"        if tm == 0x0000000f else "unknown"
        
    def swizzle_value(self):return struct.unpack(">I", self.bfres.bytes[self.offset+0x38:self.offset+0x3C])[0]

    def alignment(self):return struct.unpack(">I", self.bfres.bytes[self.offset+0x3C:self.offset+0x40])[0]

    def pitch(self):return struct.unpack(">I", self.bfres.bytes[self.offset+0x40:self.offset+0x44])[0]

    def get_relative_mipmap_offset(self, i):return struct.unpack(">I", self.bfres.bytes[self.offset+0x44+i*4:self.offset+0x48+i*4])[0]

    def get_component_selector(self):return self.bfres.bytes[self.offset+0x88:self.offset+0x8C]

    def data_offset(self):return self.offset+0xB0+struct.unpack(">i", self.bfres.bytes[self.offset+0xB0:self.offset+0xB4])[0]

    def mipmap_offset(self):return self.offset+0xB4+struct.unpack(">i", self.bfres.bytes[self.offset+0xB4:self.offset+0xB8])[0]

class BFRES():
    def __init__(self, filepath):
        f = open(filepath, "rb")
        self.bytes = f.read()
        f.close()
    def magic(self):
        return self.bytes[:4]
    def size(self):
        return struct.unpack(">I", self.bytes[0xC:0x10])[0]
    def model_index_group_offset(self):
        return 0x20+struct.unpack(">i", self.bytes[0x20:0x24])[0]
    def texture_index_group_offset(self):
        return 0x24+struct.unpack(">i", self.bytes[0x24:0x28])[0]
    def skeleton_animation_index_group_offset(self):
        return 0x28+struct.unpack(">i", self.bytes[0x28:0x2C])[0]
    def shader_parameters_index_group_offset(self):
        return 0x2C+struct.unpack(">i", self.bytes[0x2C:0x30])[0]
    def color_animation_index_group_offset(self):
        return 0x30+struct.unpack(">i", self.bytes[0x30:0x34])[0]
    def texture_srt_animation_index_group_offset(self):
        return 0x34+struct.unpack(">i", self.bytes[0x34:0x38])[0]
    def texture_pattern_animation_index_group_offset(self):
        return 0x38+struct.unpack(">i", self.bytes[0x38:0x3C])[0]
    def bone_visibility_animation_index_group_offset(self):
        return 0x3C+struct.unpack(">i", self.bytes[0x3C:0x40])[0]
    def material_visibility_animation_index_group_offset(self):
        return 0x40+struct.unpack(">i", self.bytes[0x40:0x44])[0]
    def shape_animation_index_group_offset(self):
        return 0x44+struct.unpack(">i", self.bytes[0x44:0x48])[0]
    def scene_animation_index_group_offset(self):
        return 0x48+struct.unpack(">i", self.bytes[0x48:0x4C])[0]
    def embedded_file_index_group_offset(self):
        return 0x4C+struct.unpack(">i", self.bytes[0x4C:0x50])[0]
    def model_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x50:0x52])[0]
    def texture_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x52:0x54])[0]
    def skeleton_animation_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x54:0x56])[0]
    def shader_parameters_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x56:0x58])[0]
    def color_animation_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x58:0x5A])[0]
    def texture_srt_animation_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x5A:0x5C])[0]
    def texture_pattern_animation_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x5C:0x5E])[0]
    def bone_visibility_animation_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x5E:0x60])[0]
    def material_visibility_animation_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x60:0x62])[0]
    def shape_animation_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x62:0x64])[0]
    def scene_animation_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x64:0x66])[0]
    def embedded_file_index_group_count(self):
        return struct.unpack(">H", self.bytes[0x66:0x68])[0]
    
    def get_model_name(self, i):
        offset = self.model_index_group_offset()
        name_pointer_offset = offset+0x20+i*0x10
        name_offset = name_pointer_offset+struct.unpack(">i", self.bytes[name_pointer_offset:name_pointer_offset+4])[0]
        size_of_name = struct.unpack(">i", self.bytes[name_offset-4:name_offset])[0]
        return self.bytes[name_offset:name_offset+size_of_name].decode("UTF-8")
    
    def get_model_data(self, i):
        offset = self.model_index_group_offset()
        pointer_offset = offset+0x24+i*0x10
        offset = pointer_offset+struct.unpack(">i", self.bytes[pointer_offset:pointer_offset+4])[0]
        return FMDL(offset, self)
    
    def get_texture_name(self, i):
        offset = self.texture_index_group_offset()
        name_pointer_offset = offset+0x20+i*0x10
        name_offset = name_pointer_offset+struct.unpack(">i", self.bytes[name_pointer_offset:name_pointer_offset+4])[0]
        size_of_name = struct.unpack(">i", self.bytes[name_offset-4:name_offset])[0]
        return self.bytes[name_offset:name_offset+size_of_name].decode("UTF-8")
    
    def get_texture_data(self, i):
        offset = self.texture_index_group_offset()
        pointer_offset = offset+0x24+i*0x10
        offset = pointer_offset+struct.unpack(">i", self.bytes[pointer_offset:pointer_offset+4])[0]
        return FTEX(offset, self)
    
###############################################################################################
# _parse_3x_10bit_signed ported from io_scene_bfres/src/bfres_fmdl.py by Github user RayKoopa #
###############################################################################################
def _parse_3x_10bit_signed(buffer, offset):
            integer = struct.unpack(">I", buffer[offset:offset + 4])[0]
            # 8-bit values are aligned in 'integer' as follows:
            #   Bit: 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32
            # Value:  0  1  x  x  x  x  x  x  x  x  0  1  y  y  y  y  y  y  y  y  0  1  z  z  z  z  z  z  z  z  0  0
            # Those are then divided by 511 to retrieve the decimal value.
            x = (((((integer & 0x3FC00000) >> 22) / 511)*2+0.5)%1)*2-1
            y = (((((integer & 0x000FF000) >> 12) / 511)*2+0.5)%1)*2-1
            z = (((((integer & 0x000003FC) >> 2) / 511)*2+0.5)%1)*2-1
            return x, y, z

def matrix_from_transform(pos, rot, scale):
    return Matrix.Translation(pos) * rot.to_matrix().to_4x4() * Matrix(((scale[0],0,0,0),(0,scale[1],0,0),(0,0,scale[2],0),(0,0,0,1)))

def flipMtx(mtx):
    return Matrix((\
    (mtx[0][0],mtx[1][0],mtx[2][0],mtx[3][0]),\
    (mtx[0][1],mtx[1][1],mtx[2][1],mtx[3][1]),\
    (mtx[0][2],mtx[1][2],mtx[2][2],mtx[3][2]),\
    (mtx[0][3],mtx[1][3],mtx[2][3],mtx[3][3])\
    ))
def average(floats, weights):
    tw = 0
    for w in weights:
        tw+=w
    ta = 0
    for i in range(len(floats)):
        ta += floats[i] * (weights[i]/tw)
    return ta
def averageMtx(mtxs, weights):
    return Matrix(\
(\
(average([m[0][0] for m in mtxs], weights),average([m[0][1] for m in mtxs], weights),average([m[0][2] for m in mtxs], weights),average([m[0][3] for m in mtxs], weights)),\
(average([m[1][0] for m in mtxs], weights),average([m[1][1] for m in mtxs], weights),average([m[1][2] for m in mtxs], weights),average([m[1][3] for m in mtxs], weights)),\
(average([m[2][0] for m in mtxs], weights),average([m[2][1] for m in mtxs], weights),average([m[2][2] for m in mtxs], weights),average([m[2][3] for m in mtxs], weights)),\
(average([m[3][0] for m in mtxs], weights),average([m[3][1] for m in mtxs], weights),average([m[3][2] for m in mtxs], weights),average([m[3][3] for m in mtxs], weights)),\
)\
)
def writeTextureBlock(pixels, block, tx, ty, width):
    for y in range(4):
        for x in range(4):
            if (tx*4)+x < width:
                if (((ty*4)+y)*width+((tx*4)+x))*4+4 <= len(pixels):
                    pixels[(((ty*4)+y)*width+((tx*4)+x))*4+0] = block[(y*4+x)*4+0]
                    pixels[(((ty*4)+y)*width+((tx*4)+x))*4+1] = block[(y*4+x)*4+1]
                    pixels[(((ty*4)+y)*width+((tx*4)+x))*4+2] = block[(y*4+x)*4+2]
                    pixels[(((ty*4)+y)*width+((tx*4)+x))*4+3] = block[(y*4+x)*4+3]
def writePixel(pixels, pixel, x, y, width):
    if x < width:
        if ((y*width+x)*4+4) <= len(pixels):
            pixels[(y*width+x)*4+0] = pixel[0]
            pixels[(y*width+x)*4+1] = pixel[1]
            pixels[(y*width+x)*4+2] = pixel[2]
            pixels[(y*width+x)*4+3] = pixel[3]
def decode_rgb565(bits):
    r = (bits&0xF800)>>11
    g = (bits&0x7E0)>>5
    b = bits&0x1F
    return (r/31.0,g/63.0,b/31.0)
def lerp_color(c1, c2, t):
    return (c1[0]+(c2[0]-c1[0])*t,c1[1]+(c2[1]-c1[1])*t,c1[2]+(c2[2]-c1[2])*t)
def flipY(pixels, width):
    num_pixels = len(pixels)//4
    height = num_pixels//width
    out = []
    for i in range(height-1, -1, -1):
        out += pixels[(width*4)*i:(width*4)*(i+1)]
    return out
def crop(pixels, current_width, width, height):
    out = []
    for i in range(height):
        out += pixels[((current_width)*4)*i:((current_width)*4)*i+(width*4)]
    return out

############################################
# addrlib python file by AboodXD and Exzap #
############################################

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# addrlib.py
# A Python Address Library for Wii U textures.


BCn_formats = [
    0x31, 0x431, 0x32, 0x432,
    0x33, 0x433, 0x34, 0x234,
    0x35, 0x235,
]


def swizzleSurf(width, height, height_, format_, tileMode, swizzle_,
                pitch, bitsPerPixel, data, swizzle):

    bytesPerPixel = bitsPerPixel // 8
    result = bytearray(len(data))

    if format_ in BCn_formats:
        width = (width + 3) // 4
        height = (height + 3) // 4

    for y in range(height):
        for x in range(width):
            pipeSwizzle = (swizzle_ >> 8) & 1
            bankSwizzle = (swizzle_ >> 9) & 3

            if tileMode in [0, 1]:
                pos = computeSurfaceAddrFromCoordLinear(x, y, bitsPerPixel, pitch)

            elif tileMode in [2, 3]:
                pos = computeSurfaceAddrFromCoordMicroTiled(x, y, bitsPerPixel, pitch, tileMode)

            else:
                pos = computeSurfaceAddrFromCoordMacroTiled(x, y, bitsPerPixel, pitch, height_, tileMode,
                                                            pipeSwizzle, bankSwizzle)

            pos_ = (y * width + x) * bytesPerPixel

            if pos_ + bytesPerPixel <= len(data) and pos + bytesPerPixel <= len(data):
                if swizzle == 0:
                    result[pos_:pos_ + bytesPerPixel] = data[pos:pos + bytesPerPixel]

                else:
                    result[pos:pos + bytesPerPixel] = data[pos_:pos_ + bytesPerPixel]

    return bytes(result)


def deswizzle(width, height, height_, format_, tileMode, swizzle_,
              pitch, bpp, data):

    return swizzleSurf(width, height, height_, format_, tileMode, swizzle_, pitch, bpp, data, 0)


def swizzle(width, height, height_, format_, tileMode, swizzle_,
            pitch, bpp, data):

    return swizzleSurf(width, height, height_, format_, tileMode, swizzle_, pitch, bpp, data, 1)


m_banks = 4
m_banksBitcount = 2
m_pipes = 2
m_pipesBitcount = 1
m_pipeInterleaveBytes = 256
m_pipeInterleaveBytesBitcount = 8
m_rowSize = 2048
m_swapSize = 256
m_splitSize = 2048

m_chipFamily = 2

MicroTilePixels = 64

formatHwInfo = [
    0x00, 0x00, 0x00, 0x01, 0x08, 0x03, 0x00, 0x01, 0x08, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x01, 0x10, 0x07, 0x00, 0x00, 0x10, 0x03, 0x00, 0x01, 0x10, 0x03, 0x00, 0x01,
    0x10, 0x0B, 0x00, 0x01, 0x10, 0x01, 0x00, 0x01, 0x10, 0x03, 0x00, 0x01, 0x10, 0x03, 0x00, 0x01,
    0x10, 0x03, 0x00, 0x01, 0x20, 0x03, 0x00, 0x00, 0x20, 0x07, 0x00, 0x00, 0x20, 0x03, 0x00, 0x00,
    0x20, 0x03, 0x00, 0x01, 0x20, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x03, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x20, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x01, 0x20, 0x0B, 0x00, 0x01, 0x20, 0x0B, 0x00, 0x01, 0x20, 0x0B, 0x00, 0x01,
    0x40, 0x05, 0x00, 0x00, 0x40, 0x03, 0x00, 0x00, 0x40, 0x03, 0x00, 0x00, 0x40, 0x03, 0x00, 0x00,
    0x40, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x80, 0x03, 0x00, 0x00, 0x80, 0x03, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x10, 0x01, 0x00, 0x00,
    0x10, 0x01, 0x00, 0x00, 0x20, 0x01, 0x00, 0x00, 0x20, 0x01, 0x00, 0x00, 0x20, 0x01, 0x00, 0x00,
    0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x60, 0x01, 0x00, 0x00,
    0x60, 0x01, 0x00, 0x00, 0x40, 0x01, 0x00, 0x01, 0x80, 0x01, 0x00, 0x01, 0x80, 0x01, 0x00, 0x01,
    0x40, 0x01, 0x00, 0x01, 0x80, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
]


def surfaceGetBitsPerPixel(surfaceFormat):
    hwFormat = surfaceFormat & 0x3F
    bpp = formatHwInfo[hwFormat * 4]

    return bpp


def computeSurfaceThickness(tileMode):
    thickness = 1

    if tileMode in [3, 7, 11, 13, 15]:
        thickness = 4

    elif tileMode in [16, 17]:
        thickness = 8

    return thickness


def computePixelIndexWithinMicroTile(x, y, bpp, tileMode):
    z = 0
    pixelBit6 = 0
    pixelBit7 = 0
    pixelBit8 = 0
    thickness = computeSurfaceThickness(tileMode)

    if bpp == 0x08:
        pixelBit0 = x & 1
        pixelBit1 = (x & 2) >> 1
        pixelBit2 = (x & 4) >> 2
        pixelBit3 = (y & 2) >> 1
        pixelBit4 = y & 1
        pixelBit5 = (y & 4) >> 2

    elif bpp == 0x10:
        pixelBit0 = x & 1
        pixelBit1 = (x & 2) >> 1
        pixelBit2 = (x & 4) >> 2
        pixelBit3 = y & 1
        pixelBit4 = (y & 2) >> 1
        pixelBit5 = (y & 4) >> 2

    elif bpp in [0x20, 0x60]:
        pixelBit0 = x & 1
        pixelBit1 = (x & 2) >> 1
        pixelBit2 = y & 1
        pixelBit3 = (x & 4) >> 2
        pixelBit4 = (y & 2) >> 1
        pixelBit5 = (y & 4) >> 2

    elif bpp == 0x40:
        pixelBit0 = x & 1
        pixelBit1 = y & 1
        pixelBit2 = (x & 2) >> 1
        pixelBit3 = (x & 4) >> 2
        pixelBit4 = (y & 2) >> 1
        pixelBit5 = (y & 4) >> 2

    elif bpp == 0x80:
        pixelBit0 = y & 1
        pixelBit1 = x & 1
        pixelBit2 = (x & 2) >> 1
        pixelBit3 = (x & 4) >> 2
        pixelBit4 = (y & 2) >> 1
        pixelBit5 = (y & 4) >> 2

    else:
        pixelBit0 = x & 1
        pixelBit1 = (x & 2) >> 1
        pixelBit2 = y & 1
        pixelBit3 = (x & 4) >> 2
        pixelBit4 = (y & 2) >> 1
        pixelBit5 = (y & 4) >> 2

    if thickness > 1:
        pixelBit6 = z & 1
        pixelBit7 = (z & 2) >> 1

    if thickness == 8:
        pixelBit8 = (z & 4) >> 2

    return ((pixelBit8 << 8) | (pixelBit7 << 7) | (pixelBit6 << 6) |
            32 * pixelBit5 | 16 * pixelBit4 | 8 * pixelBit3 |
            4 * pixelBit2 | pixelBit0 | 2 * pixelBit1)


def computePipeFromCoordWoRotation(x, y):
    # hardcoded to assume 2 pipes
    return ((y >> 3) ^ (x >> 3)) & 1


def computeBankFromCoordWoRotation(x, y):
    numPipes = m_pipes
    numBanks = m_banks
    bank = 0

    if numBanks == 4:
        bankBit0 = ((y // (16 * numPipes)) ^ (x >> 3)) & 1
        bank = bankBit0 | 2 * (((y // (8 * numPipes)) ^ (x >> 4)) & 1)

    elif numBanks == 8:
        bankBit0a = ((y // (32 * numPipes)) ^ (x >> 3)) & 1
        bank = (bankBit0a | 2 * (((y // (32 * numPipes)) ^ (y // (16 * numPipes) ^ (x >> 4))) & 1) |
                4 * (((y // (8 * numPipes)) ^ (x >> 5)) & 1))

    return bank


def isThickMacroTiled(tileMode):
    thickMacroTiled = 0

    if tileMode in [7, 11, 13, 15]:
        thickMacroTiled = 1

    return thickMacroTiled


def isBankSwappedTileMode(tileMode):
    bankSwapped = 0

    if tileMode in [8, 9, 10, 11, 14, 15]:
        bankSwapped = 1

    return bankSwapped


def computeMacroTileAspectRatio(tileMode):
    ratio = 1

    if tileMode in [8, 12, 14]:
        ratio = 1

    elif tileMode in [5, 9]:
        ratio = 2

    elif tileMode in [6, 10]:
        ratio = 4

    return ratio


def computeSurfaceBankSwappedWidth(tileMode, bpp, pitch, numSamples=1):
    if isBankSwappedTileMode(tileMode) == 0:
        return 0

    numBanks = m_banks
    numPipes = m_pipes
    swapSize = m_swapSize
    rowSize = m_rowSize
    splitSize = m_splitSize
    groupSize = m_pipeInterleaveBytesBitcount
    bytesPerSample = 8 * bpp

    if bytesPerSample != 0:
        samplesPerTile = splitSize // bytesPerSample
        slicesPerTile = max(1, numSamples // samplesPerTile)
    else:
        slicesPerTile = 1

    if isThickMacroTiled(tileMode) != 0:
        numSamples = 4

    bytesPerTileSlice = numSamples * bytesPerSample // slicesPerTile

    factor = computeMacroTileAspectRatio(tileMode)
    swapTiles = max(1, (swapSize >> 1) // bpp)

    swapWidth = swapTiles * 8 * numBanks
    heightBytes = numSamples * factor * numPipes * bpp // slicesPerTile
    swapMax = numPipes * numBanks * rowSize // heightBytes
    swapMin = groupSize * 8 * numBanks // bytesPerTileSlice

    bankSwapWidth = min(swapMax, max(swapMin, swapWidth))

    while bankSwapWidth >= 2 * pitch:
        bankSwapWidth >>= 1

    return bankSwapWidth


def computeSurfaceAddrFromCoordLinear(x, y, bpp, pitch):
    rowOffset = y * pitch
    pixOffset = x

    addr = (rowOffset + pixOffset) * bpp
    addr //= 8

    return addr


def computeSurfaceAddrFromCoordMicroTiled(x, y, bpp, pitch, tileMode):
    microTileThickness = 1

    if tileMode == 3:
        microTileThickness = 4

    microTileBytes = (MicroTilePixels * microTileThickness * bpp + 7) // 8
    microTilesPerRow = pitch >> 3
    microTileIndexX = x >> 3
    microTileIndexY = y >> 3

    microTileOffset = microTileBytes * (microTileIndexX + microTileIndexY * microTilesPerRow)

    pixelIndex = computePixelIndexWithinMicroTile(x, y, bpp, tileMode)

    pixelOffset = bpp * pixelIndex
    pixelOffset >>= 3

    return pixelOffset + microTileOffset


bankSwapOrder = [0, 1, 3, 2, 6, 7, 5, 4, 0, 0]


def computeSurfaceAddrFromCoordMacroTiled(x, y, bpp, pitch, height,
                                          tileMode, pipeSwizzle,
                                          bankSwizzle):

    numPipes = m_pipes
    numBanks = m_banks
    numGroupBits = m_pipeInterleaveBytesBitcount
    numPipeBits = m_pipesBitcount
    numBankBits = m_banksBitcount

    microTileThickness = computeSurfaceThickness(tileMode)

    microTileBits = bpp * (microTileThickness * MicroTilePixels)
    microTileBytes = (microTileBits + 7) // 8

    pixelIndex = computePixelIndexWithinMicroTile(x, y, bpp, tileMode)

    pixelOffset = bpp * pixelIndex

    elemOffset = pixelOffset

    bytesPerSample = microTileBytes

    if microTileBytes <= m_splitSize:
        numSamples = 1
        sampleSlice = 0

    else:
        samplesPerSlice = m_splitSize // bytesPerSample
        numSampleSplits = max(1, 1 // samplesPerSlice)
        numSamples = samplesPerSlice
        sampleSlice = elemOffset // (microTileBits // numSampleSplits)
        elemOffset %= microTileBits // numSampleSplits

    elemOffset += 7
    elemOffset //= 8

    pipe = computePipeFromCoordWoRotation(x, y)
    bank = computeBankFromCoordWoRotation(x, y)

    bankPipe = pipe + numPipes * bank

    swizzle_ = pipeSwizzle + numPipes * bankSwizzle

    bankPipe ^= numPipes * sampleSlice * ((numBanks >> 1) + 1) ^ swizzle_
    bankPipe %= numPipes * numBanks
    pipe = bankPipe % numPipes
    bank = bankPipe // numPipes

    sliceBytes = (height * pitch * microTileThickness * bpp * numSamples + 7) // 8
    sliceOffset = sliceBytes * (sampleSlice // microTileThickness)

    macroTilePitch = 8 * m_banks
    macroTileHeight = 8 * m_pipes

    if tileMode in [5, 9]:  # GX2_TILE_MODE_2D_TILED_THIN2 and GX2_TILE_MODE_2B_TILED_THIN2
        macroTilePitch >>= 1
        macroTileHeight *= 2

    elif tileMode in [6, 10]:  # GX2_TILE_MODE_2D_TILED_THIN4 and GX2_TILE_MODE_2B_TILED_THIN4
        macroTilePitch >>= 2
        macroTileHeight *= 4

    macroTilesPerRow = pitch // macroTilePitch
    macroTileBytes = (numSamples * microTileThickness * bpp * macroTileHeight
                      * macroTilePitch + 7) // 8
    macroTileIndexX = x // macroTilePitch
    macroTileIndexY = y // macroTileHeight
    macroTileOffset = (macroTileIndexX + macroTilesPerRow * macroTileIndexY) * macroTileBytes

    if tileMode in [8, 9, 10, 11, 14, 15]:
        bankSwapWidth = computeSurfaceBankSwappedWidth(tileMode, bpp, pitch)
        swapIndex = macroTilePitch * macroTileIndexX // bankSwapWidth
        bank ^= bankSwapOrder[swapIndex & (m_banks - 1)]

    groupMask = ((1 << numGroupBits) - 1)

    numSwizzleBits = (numBankBits + numPipeBits)

    totalOffset = (elemOffset + ((macroTileOffset + sliceOffset) >> numSwizzleBits))

    offsetHigh = (totalOffset & ~groupMask) << numSwizzleBits
    offsetLow = groupMask & totalOffset

    pipeBits = pipe << numGroupBits
    bankBits = bank << (numPipeBits + numGroupBits)

    return bankBits | pipeBits | offsetLow | offsetHigh


ADDR_OK = 0

expPitch = 0
expHeight = 0
expNumSlices = 0

m_configFlags = 4


class Flags:
    def __init__(self):
        self.value = 0


class tileInfo:
    def __init__(self):
        self.banks = 0
        self.bankWidth = 0
        self.bankHeight = 0
        self.macroAspectRatio = 0
        self.tileSplitBytes = 0
        self.pipeConfig = 0


class surfaceIn:
    def __init__(self):
        self.size = 0
        self.tileMode = 0
        self.format = 0
        self.bpp = 0
        self.numSamples = 0
        self.width = 0
        self.height = 0
        self.numSlices = 0
        self.slice = 0
        self.mipLevel = 0
        self.flags = Flags()
        self.numFrags = 0
        self.pTileInfo = tileInfo()
        self.tileIndex = 0


class surfaceOut:
    def __init__(self):
        self.size = 0
        self.pitch = 0
        self.height = 0
        self.depth = 0
        self.surfSize = 0
        self.tileMode = 0
        self.baseAlign = 0
        self.pitchAlign = 0
        self.heightAlign = 0
        self.depthAlign = 0
        self.bpp = 0
        self.pixelPitch = 0
        self.pixelHeight = 0
        self.pixelBits = 0
        self.sliceSize = 0
        self.pitchTileMax = 0
        self.heightTileMax = 0
        self.sliceTileMax = 0
        self.pTileInfo = tileInfo()
        self.tileType = 0
        self.tileIndex = 0


pIn = surfaceIn()
pOut = surfaceOut()


def getFillSizeFieldsFlags():
    return (m_configFlags >> 6) & 1


def getSliceComputingFlags():
    return (m_configFlags >> 4) & 3


def powTwoAlign(x, align):
    return ~(align - 1) & (x + align - 1)


def nextPow2(dim):
    newDim = 1
    if dim <= 0x7FFFFFFF:
        while newDim < dim:
            newDim *= 2

    else:
        newDim = 2147483648

    return newDim


def useTileIndex(index):
    if (m_configFlags >> 7) & 1 and index != -1:
        return 1

    else:
        return 0


def getBitsPerPixel(format_):
    expandY = 1
    elemMode = 3

    if format_ == 1:
        bpp = 8
        expandX = 1

    elif format_ in [5, 6, 7, 8, 9, 10, 11]:
        bpp = 16
        expandX = 1

    elif format_ == 39:
        elemMode = 7
        bpp = 16
        expandX = 1

    elif format_ == 40:
        elemMode = 8
        bpp = 16
        expandX = 1

    elif format_ in [13, 14, 15, 16, 19, 20, 21, 23, 25, 26]:
        bpp = 32
        expandX = 1

    elif format_ in [29, 30, 31, 32, 62]:
        bpp = 64
        expandX = 1

    elif format_ in [34, 35]:
        bpp = 128
        expandX = 1

    elif format_ == 0:
        bpp = 0
        expandX = 1

    elif format_ == 38:
        elemMode = 6
        bpp = 1
        expandX = 8

    elif format_ == 37:
        elemMode = 5
        bpp = 1
        expandX = 8

    elif format_ in [2, 3]:
        bpp = 8
        expandX = 1

    elif format_ == 12:
        bpp = 16
        expandX = 1

    elif format_ in [17, 18, 22, 24, 27, 41, 42, 43]:
        bpp = 32
        expandX = 1

    elif format_ == 28:
        bpp = 64
        expandX = 1

    elif format_ == 44:
        elemMode = 4
        bpp = 24
        expandX = 3

    elif format_ in [45, 46]:
        elemMode = 4
        bpp = 48
        expandX = 3

    elif format_ in [47, 48]:
        elemMode = 4
        bpp = 96
        expandX = 3

    elif format_ == 49:
        elemMode = 9
        expandY = 4
        bpp = 64
        expandX = 4

    elif format_ == 52:
        elemMode = 12
        expandY = 4
        bpp = 64
        expandX = 4

    elif format_ == 50:
        elemMode = 10
        expandY = 4
        bpp = 128
        expandX = 4

    elif format_ == 51:
        elemMode = 11
        expandY = 4
        bpp = 128
        expandX = 4

    elif format_ in [53, 54, 55]:
        elemMode = 13
        expandY = 4
        bpp = 128
        expandX = 4

    else:
        bpp = 0
        expandX = 1

    return bpp, expandX, expandY, elemMode


def adjustSurfaceInfo(elemMode, expandX, expandY, pBpp, pWidth, pHeight):
    bBCnFormat = 0

    if pBpp:
        bpp = pBpp

        if elemMode == 4:
            packedBits = bpp // expandX // expandY

        elif elemMode in [5, 6]:
            packedBits = expandY * expandX * bpp

        elif elemMode in [7, 8]:
            packedBits = pBpp

        elif elemMode in [9, 12]:
            packedBits = 64
            bBCnFormat = 1

        elif elemMode in [10, 11, 13]:
            bBCnFormat = 1
            packedBits = 128

        elif elemMode in [0, 1, 2, 3]:
            packedBits = pBpp

        else:
            packedBits = pBpp

        pIn.bpp = packedBits

    if pWidth:
        if pHeight:
            width = pWidth
            height = pHeight

            if expandX > 1 or expandY > 1:
                if elemMode == 4:
                    widtha = expandX * width
                    heighta = expandY * height

                elif bBCnFormat:
                    widtha = width // expandX
                    heighta = height // expandY

                else:
                    widtha = (width + expandX - 1) // expandX
                    heighta = (height + expandY - 1) // expandY

                pIn.width = max(1, widtha)
                pIn.height = max(1, heighta)

    return packedBits


def hwlComputeMipLevel():
    handled = 0

    if 49 <= pIn.format <= 55:
        if pIn.mipLevel:
            width = pIn.width
            height = pIn.height
            slices = pIn.numSlices

            if (pIn.flags.value >> 12) & 1:
                widtha = width >> pIn.mipLevel
                heighta = height >> pIn.mipLevel

                if not ((pIn.flags.value >> 4) & 1):
                    slices >>= pIn.mipLevel

                width = max(1, widtha)
                height = max(1, heighta)
                slices = max(1, slices)

            pIn.width = nextPow2(width)
            pIn.height = nextPow2(height)
            pIn.numSlices = slices

        handled = 1

    return handled


def computeMipLevel():
    slices = 0
    height = 0
    width = 0
    hwlHandled = 0

    if 49 <= pIn.format <= 55 and (not pIn.mipLevel or ((pIn.flags.value >> 12) & 1)):
        pIn.width = powTwoAlign(pIn.width, 4)
        pIn.height = powTwoAlign(pIn.height, 4)

    hwlHandled = hwlComputeMipLevel()
    if not hwlHandled and pIn.mipLevel and ((pIn.flags.value >> 12) & 1):
        width = pIn.width
        height = pIn.height
        slices = pIn.numSlices
        width >>= pIn.mipLevel
        height >>= pIn.mipLevel

        if not ((pIn.flags.value >> 4) & 1):
            slices >>= pIn.mipLevel

        width = max(1, width)
        height = max(1, height)
        slices = max(1, slices)

        if pIn.format not in [47, 48]:
            width = nextPow2(width)
            height = nextPow2(height)
            slices = nextPow2(slices)

        pIn.width = width
        pIn.height = height
        pIn.numSlices = slices


def convertToNonBankSwappedMode(tileMode):
    if tileMode == 8:
        expTileMode = 4

    elif tileMode == 9:
        expTileMode = 5

    elif tileMode == 10:
        expTileMode = 6

    elif tileMode == 11:
        expTileMode = 7

    elif tileMode == 14:
        expTileMode = 12

    elif tileMode == 15:
        expTileMode = 13

    else:
        expTileMode = tileMode

    return expTileMode


def computeSurfaceTileSlices(tileMode, bpp, numSamples):
    bytePerSample = ((bpp << 6) + 7) >> 3
    tileSlices = 1

    if computeSurfaceThickness(tileMode) > 1:
        numSamples = 4

    if bytePerSample:
        samplePerTile = m_splitSize // bytePerSample
        if samplePerTile:
            tileSlices = max(1, numSamples // samplePerTile)

    return tileSlices


def computeSurfaceRotationFromTileMode(tileMode):
    pipes = m_pipes
    result = 0

    if tileMode in [4, 5, 6, 7, 8, 9, 10, 11]:
        result = pipes * ((m_banks >> 1) - 1)

    elif tileMode in [12, 13, 14, 15]:
        result = 1

    return result


def computeSurfaceMipLevelTileMode(baseTileMode, bpp, level, width, height, numSlices, numSamples, isDepth, noRecursive):
    expTileMode = baseTileMode
    numPipes = m_pipes
    numBanks = m_banks
    groupBytes = m_pipeInterleaveBytes
    tileSlices = computeSurfaceTileSlices(baseTileMode, bpp, numSamples)

    if baseTileMode == 5:
        if 2 * m_pipeInterleaveBytes > m_splitSize:
            expTileMode = 4

    elif baseTileMode == 6:
        if 4 * m_pipeInterleaveBytes > m_splitSize:
            expTileMode = 5

    elif baseTileMode == 7:
        if numSamples > 1 or tileSlices > 1 or isDepth:
            expTileMode = 4

    elif baseTileMode == 13:
        if numSamples > 1 or tileSlices > 1 or isDepth:
            expTileMode = 12

    elif baseTileMode == 9:
        if 2 * m_pipeInterleaveBytes > m_splitSize:
            expTileMode = 8

    elif baseTileMode == 10:
        if 4 * m_pipeInterleaveBytes > m_splitSize:
            expTileMode = 9

    elif baseTileMode == 11:
        if numSamples > 1 or tileSlices > 1 or isDepth:
            expTileMode = 8

    elif baseTileMode == 15:
        if numSamples > 1 or tileSlices > 1 or isDepth:
            expTileMode = 14

    elif baseTileMode == 2:
        if numSamples > 1 and ((m_configFlags >> 2) & 1):
            expTileMode = 4

    elif baseTileMode == 3:
        if numSamples > 1 or isDepth:
            expTileMode = 2

        if numSamples in [2, 4]:
            expTileMode = 7

    else:
        expTileMode = baseTileMode

    rotation = computeSurfaceRotationFromTileMode(expTileMode)
    if not (rotation % m_pipes):
        if expTileMode == 12:
            expTileMode = 4

        if expTileMode == 14:
            expTileMode = 8

        if expTileMode == 13:
            expTileMode = 7

        if expTileMode == 15:
            expTileMode = 11

    if noRecursive:
        result = expTileMode

    else:
        if bpp in [24, 48, 96]:
            bpp //= 3

        widtha = nextPow2(width)
        heighta = nextPow2(height)
        numSlicesa = nextPow2(numSlices)

        if level:
            expTileMode = convertToNonBankSwappedMode(expTileMode)
            thickness = computeSurfaceThickness(expTileMode)
            microTileBytes = (numSamples * bpp * (thickness << 6) + 7) >> 3

            if microTileBytes >= groupBytes:
                v13 = 1

            else:
                v13 = groupBytes // microTileBytes

            widthAlignFactor = v13
            macroTileWidth = 8 * numBanks
            macroTileHeight = 8 * numPipes

            if expTileMode in [4, 12]:
                if (widtha < widthAlignFactor * macroTileWidth) or heighta < macroTileHeight:
                    expTileMode = 2

            elif expTileMode == 5:
                macroTileWidth >>= 1
                macroTileHeight *= 2

                if (widtha < widthAlignFactor * macroTileWidth) or heighta < macroTileHeight:
                    expTileMode = 2

            elif expTileMode == 6:
                macroTileWidth >>= 2
                macroTileHeight *= 4

                if (widtha < widthAlignFactor * macroTileWidth) or heighta < macroTileHeight:
                    expTileMode = 2

            if expTileMode in [7, 13]:
                if (widtha < widthAlignFactor * macroTileWidth) or heighta < macroTileHeight:
                    expTileMode = 3

            v11 = expTileMode
            if expTileMode == 3:
                if numSlicesa < 4:
                    expTileMode = 2

            elif v11 == 7:
                if numSlicesa < 4:
                    expTileMode = 4

            elif v11 == 13 and numSlicesa < 4:
                expTileMode = 12

            result = computeSurfaceMipLevelTileMode(
                expTileMode,
                bpp,
                level,
                widtha,
                heighta,
                numSlicesa,
                numSamples,
                isDepth,
                1)

        else:
            result = expTileMode

    return result


def isDualPitchAlignNeeded(tileMode, isDepth, mipLevel):
    if isDepth or mipLevel or m_chipFamily != 1:
        needed = 0

    elif tileMode in [0, 1, 2, 3, 7, 11, 13, 15]:
        needed = 0

    else:
        needed = 1

    return needed


def isPow2(dim):
    if dim & (dim - 1) == 0:
        return 1

    else:
        return 0


def padDimensions(tileMode, padDims, isCube, cubeAsArray, pitchAlign, heightAlign, sliceAlign):
    global expPitch
    global expHeight
    global expNumSlices

    thickness = computeSurfaceThickness(tileMode)
    if not padDims:
        padDims = 3

    if isPow2(pitchAlign):
        expPitch = powTwoAlign(expPitch, pitchAlign)

    else:
        expPitch = pitchAlign + expPitch - 1
        expPitch //= pitchAlign
        expPitch *= pitchAlign

    if padDims > 1:
        expHeight = powTwoAlign(expHeight, heightAlign)

    if padDims > 2 or thickness > 1:
        if isCube and ((not ((m_configFlags >> 3) & 1)) or cubeAsArray):
            expNumSlices = nextPow2(expNumSlices)

        if thickness > 1:
            expNumSlices = powTwoAlign(expNumSlices, sliceAlign)

    return expPitch, expHeight, expNumSlices


def adjustPitchAlignment(flags, pitchAlign):
    if (flags.value >> 13) & 1:
        pitchAlign = powTwoAlign(pitchAlign, 0x20)

    return pitchAlign


def computeSurfaceAlignmentsLinear(tileMode, bpp, flags):
    if tileMode:
        if tileMode == 1:
            pixelsPerPipeInterleave = 8 * m_pipeInterleaveBytes // bpp
            baseAlign = m_pipeInterleaveBytes
            pitchAlign = max(0x40, pixelsPerPipeInterleave)
            heightAlign = 1

        else:
            baseAlign = 1
            pitchAlign = 1
            heightAlign = 1

    else:
        baseAlign = 1
        pitchAlign = (1 if bpp != 1 else 8)
        heightAlign = 1

    pitchAlign = adjustPitchAlignment(flags, pitchAlign)

    return baseAlign, pitchAlign, heightAlign


def computeSurfaceInfoLinear(tileMode, bpp, numSamples, pitch, height, numSlices, mipLevel, padDims, flags):
    global expPitch
    global expHeight
    global expNumSlices

    expPitch = pitch
    expHeight = height
    expNumSlices = numSlices

    valid = 1
    microTileThickness = computeSurfaceThickness(tileMode)

    baseAlign, pitchAlign, heightAlign = computeSurfaceAlignmentsLinear(tileMode, bpp, flags)

    if ((flags.value >> 9) & 1) and not mipLevel:
        expPitch //= 3
        expPitch = nextPow2(expPitch)

    if mipLevel:
        expPitch = nextPow2(expPitch)
        expHeight = nextPow2(expHeight)

        if (flags.value >> 4) & 1:
            expNumSlices = numSlices

            if numSlices <= 1:
                padDims = 2

            else:
                padDims = 0

        else:
            expNumSlices = nextPow2(numSlices)

    expPitch, expHeight, expNumSlices = padDimensions(
        tileMode,
        padDims,
        (flags.value >> 4) & 1,
        (flags.value >> 7) & 1,
        pitchAlign,
        heightAlign,
        microTileThickness)

    if ((flags.value >> 9) & 1) and not mipLevel:
        expPitch *= 3

    slices = expNumSlices * numSamples // microTileThickness
    pPitchOut = expPitch
    pHeightOut = expHeight
    pNumSlicesOut = expNumSlices
    pSurfSize = (expHeight * expPitch * slices * bpp * numSamples + 7) // 8
    pBaseAlign = baseAlign
    pPitchAlign = pitchAlign
    pHeightAlign = heightAlign
    pDepthAlign = microTileThickness

    return valid, pPitchOut, pHeightOut, pNumSlicesOut, pSurfSize, pBaseAlign, pPitchAlign, pHeightAlign, pDepthAlign


def computeSurfaceAlignmentsMicroTiled(tileMode, bpp, flags, numSamples):
    if bpp in [24, 48, 96]:
        bpp //= 3

    v8 = computeSurfaceThickness(tileMode)
    baseAlign = m_pipeInterleaveBytes
    pitchAlign = max(8, m_pipeInterleaveBytes // bpp // numSamples // v8)
    heightAlign = 8

    pitchAlign = adjustPitchAlignment(flags, pitchAlign)

    return baseAlign, pitchAlign, heightAlign


def computeSurfaceInfoMicroTiled(tileMode, bpp, numSamples, pitch, height, numSlices, mipLevel, padDims, flags):
    global expPitch
    global expHeight
    global expNumSlices

    expTileMode = tileMode
    expPitch = pitch
    expHeight = height
    expNumSlices = numSlices

    valid = 1
    microTileThickness = computeSurfaceThickness(tileMode)

    if mipLevel:
        expPitch = nextPow2(pitch)
        expHeight = nextPow2(height)
        if (flags.value >> 4) & 1:
            expNumSlices = numSlices

            if numSlices <= 1:
                padDims = 2

            else:
                padDims = 0

        else:
            expNumSlices = nextPow2(numSlices)

        if expTileMode == 3 and expNumSlices < 4:
            expTileMode = 2
            microTileThickness = 1

    baseAlign, pitchAlign, heightAlign = computeSurfaceAlignmentsMicroTiled(
        expTileMode,
        bpp,
        flags,
        numSamples)

    expPitch, expHeight, expNumSlices = padDimensions(
        expTileMode,
        padDims,
        (flags.value >> 4) & 1,
        (flags.value >> 7) & 1,
        pitchAlign,
        heightAlign,
        microTileThickness)

    pPitchOut = expPitch
    pHeightOut = expHeight
    pNumSlicesOut = expNumSlices
    pSurfSize = (expHeight * expPitch * expNumSlices * bpp * numSamples + 7) // 8
    pTileModeOut = expTileMode
    pBaseAlign = baseAlign
    pPitchAlign = pitchAlign
    pHeightAlign = heightAlign
    pDepthAlign = microTileThickness

    return valid, pPitchOut, pHeightOut, pNumSlicesOut, pSurfSize, pTileModeOut, pBaseAlign, pPitchAlign, pHeightAlign, pDepthAlign


def isDualBaseAlignNeeded(tileMode):
    needed = 1

    if m_chipFamily == 1:
        if 0 <= tileMode <= 3:
            needed = 0

    else:
        needed = 0

    return needed


def computeSurfaceAlignmentsMacroTiled(tileMode, bpp, flags, numSamples):
    groupBytes = m_pipeInterleaveBytes
    numBanks = m_banks
    numPipes = m_pipes
    splitBytes = m_splitSize
    aspectRatio = computeMacroTileAspectRatio(tileMode)
    thickness = computeSurfaceThickness(tileMode)

    if bpp in [24, 48, 96]:
        bpp //= 3

    if bpp == 3:
        bpp = 1

    macroTileWidth = 8 * numBanks // aspectRatio
    macroTileHeight = aspectRatio * 8 * numPipes

    pitchAlign = max(macroTileWidth, macroTileWidth * (groupBytes // bpp // (8 * thickness) // numSamples))
    pitchAlign = adjustPitchAlignment(flags, pitchAlign)

    heightAlign = macroTileHeight
    macroTileBytes = numSamples * ((bpp * macroTileHeight * macroTileWidth + 7) >> 3)

    if m_chipFamily == 1 and numSamples == 1:
        macroTileBytes *= 2

    if thickness == 1:
        baseAlign = max(macroTileBytes, (numSamples * heightAlign * bpp * pitchAlign + 7) >> 3)

    else:
        baseAlign = max(groupBytes, (4 * heightAlign * bpp * pitchAlign + 7) >> 3)

    microTileBytes = (thickness * numSamples * (bpp << 6) + 7) >> 3
    numSlicesPerMicroTile = 1 if microTileBytes < splitBytes else microTileBytes // splitBytes
    baseAlign //= numSlicesPerMicroTile

    if isDualBaseAlignNeeded(tileMode):
        macroBytes = (bpp * macroTileHeight * macroTileWidth + 7) >> 3

        if baseAlign // macroBytes % 2:
            baseAlign += macroBytes

    return baseAlign, pitchAlign, heightAlign, macroTileWidth, macroTileHeight


def computeSurfaceInfoMacroTiled(tileMode, baseTileMode, bpp, numSamples, pitch, height, numSlices, mipLevel, padDims, flags):
    global expPitch
    global expHeight
    global expNumSlices

    expPitch = pitch
    expHeight = height
    expNumSlices = numSlices

    valid = 1
    expTileMode = tileMode
    microTileThickness = computeSurfaceThickness(tileMode)

    if mipLevel:
        expPitch = nextPow2(pitch)
        expHeight = nextPow2(height)

        if (flags.value >> 4) & 1:
            expNumSlices = numSlices
            padDims = 2 if numSlices <= 1 else 0

        else:
            expNumSlices = nextPow2(numSlices)

        if expTileMode == 7 and expNumSlices < 4:
            expTileMode = 4
            microTileThickness = 1

    if (tileMode == baseTileMode
        or not mipLevel
        or not isThickMacroTiled(baseTileMode)
        or isThickMacroTiled(tileMode)):
        baseAlign, pitchAlign, heightAlign, macroWidth, macroHeight = computeSurfaceAlignmentsMacroTiled(
            tileMode,
            bpp,
            flags,
            numSamples)

        bankSwappedWidth = computeSurfaceBankSwappedWidth(tileMode, bpp, pitch, numSamples)

        if bankSwappedWidth > pitchAlign:
            pitchAlign = bankSwappedWidth

        if isDualPitchAlignNeeded(tileMode, (flags.value >> 1) & 1, mipLevel):
            v21 = (m_pipeInterleaveBytes >> 3) // bpp // numSamples
            tilePerGroup = v21 // computeSurfaceThickness(tileMode)

            if not tilePerGroup:
                tilePerGroup = 1

            evenHeight = (expHeight - 1) // macroHeight & 1
            evenWidth = (expPitch - 1) // macroWidth & 1

            if (numSamples == 1
                and tilePerGroup == 1
                and not evenWidth
                and (expPitch > macroWidth or not evenHeight and expHeight > macroHeight)):
                expPitch += macroWidth

        expPitch, expHeight, expNumSlices = padDimensions(
            tileMode,
            padDims,
            (flags.value >> 4) & 1,
            (flags.value >> 7) & 1,
            pitchAlign,
            heightAlign,
            microTileThickness)

        pPitchOut = expPitch
        pHeightOut = expHeight
        pNumSlicesOut = expNumSlices
        pSurfSize = (expHeight * expPitch * expNumSlices * bpp * numSamples + 7) // 8
        pTileModeOut = expTileMode
        pBaseAlign = baseAlign
        pPitchAlign = pitchAlign
        pHeightAlign = heightAlign
        pDepthAlign = microTileThickness
        result = valid

    else:
        baseAlign, pitchAlign, heightAlign, macroWidth, macroHeight = computeSurfaceAlignmentsMacroTiled(
            baseTileMode,
            bpp,
            flags,
            numSamples)

        pitchAlignFactor = (m_pipeInterleaveBytes >> 3) // bpp
        if not pitchAlignFactor:
            pitchAlignFactor = 1

        if expPitch < pitchAlign * pitchAlignFactor or expHeight < heightAlign:
            expTileMode = 2

            result, pPitchOut, pHeightOut, pNumSlicesOut, pSurfSize, pTileModeOut, pBaseAlign, pPitchAlign, pHeightAlign, pDepthAlign = computeSurfaceInfoMicroTiled(
                2,
                bpp,
                numSamples,
                pitch,
                height,
                numSlices,
                mipLevel,
                padDims,
                flags)

        else:
            baseAlign, pitchAlign, heightAlign, macroWidth, macroHeight = computeSurfaceAlignmentsMacroTiled(
                tileMode,
                bpp,
                flags,
                numSamples)

            bankSwappedWidth = computeSurfaceBankSwappedWidth(tileMode, bpp, pitch, numSamples)
            if bankSwappedWidth > pitchAlign:
                pitchAlign = bankSwappedWidth

            if isDualPitchAlignNeeded(tileMode, (flags.value >> 1) & 1, mipLevel):
                v21 = (m_pipeInterleaveBytes >> 3) // bpp // numSamples
                tilePerGroup = v21 // computeSurfaceThickness(tileMode)

                if not tilePerGroup:
                    tilePerGroup = 1

                evenHeight = (expHeight - 1) // macroHeight & 1
                evenWidth = (expPitch - 1) // macroWidth & 1

                if numSamples == 1 and tilePerGroup == 1 and not evenWidth and (expPitch > macroWidth or not evenHeight and expHeight > macroHeight):
                    expPitch += macroWidth

            expPitch, expHeight, expNumSlices = padDimensions(
                tileMode,
                padDims,
                (flags.value >> 4) & 1,
                (flags.value >> 7) & 1,
                pitchAlign,
                heightAlign,
                microTileThickness)

            pPitchOut = expPitch
            pHeightOut = expHeight
            pNumSlicesOut = expNumSlices
            pSurfSize = (expHeight * expPitch * expNumSlices * bpp * numSamples + 7) // 8
            pTileModeOut = expTileMode
            pBaseAlign = baseAlign
            pPitchAlign = pitchAlign
            pHeightAlign = heightAlign
            pDepthAlign = microTileThickness
            result = valid

    return result, pPitchOut, pHeightOut, pNumSlicesOut, pSurfSize, pTileModeOut, pBaseAlign, pPitchAlign, pHeightAlign, pDepthAlign


def ComputeSurfaceInfoEx():
    tileMode = pIn.tileMode
    bpp = pIn.bpp
    numSamples = max(1, pIn.numSamples)
    pitch = pIn.width
    height = pIn.height
    numSlices = pIn.numSlices
    mipLevel = pIn.mipLevel
    flags = Flags()
    flags.value = pIn.flags.value
    pPitchOut = pOut.pitch
    pHeightOut = pOut.height
    pNumSlicesOut = pOut.depth
    pTileModeOut = pOut.tileMode
    pSurfSize = pOut.surfSize
    pBaseAlign = pOut.baseAlign
    pPitchAlign = pOut.pitchAlign
    pHeightAlign = pOut.heightAlign
    pDepthAlign = pOut.depthAlign
    padDims = 0
    valid = 0
    baseTileMode = tileMode

    if ((flags.value >> 4) & 1) and not mipLevel:
        padDims = 2

    if ((flags.value >> 6) & 1):
        tileMode = convertToNonBankSwappedMode(tileMode)

    else:
        tileMode = computeSurfaceMipLevelTileMode(
            tileMode,
            bpp,
            mipLevel,
            pitch,
            height,
            numSlices,
            numSamples,
            (flags.value >> 1) & 1,
            0)

    if tileMode in [0, 1]:
        valid, pPitchOut, pHeightOut, pNumSlicesOut, pSurfSize, pBaseAlign, pPitchAlign, pHeightAlign, pDepthAlign = computeSurfaceInfoLinear(
            tileMode,
            bpp,
            numSamples,
            pitch,
            height,
            numSlices,
            mipLevel,
            padDims,
            flags)

        pTileModeOut = tileMode

    elif tileMode in [2, 3]:
        valid, pPitchOut, pHeightOut, pNumSlicesOut, pSurfSize, pTileModeOut, pBaseAlign, pPitchAlign, pHeightAlign, pDepthAlign = computeSurfaceInfoMicroTiled(
            tileMode,
            bpp,
            numSamples,
            pitch,
            height,
            numSlices,
            mipLevel,
            padDims,
            flags)

    elif tileMode in [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]:
        valid, pPitchOut, pHeightOut, pNumSlicesOut, pSurfSize, pTileModeOut, pBaseAlign, pPitchAlign, pHeightAlign, pDepthAlign = computeSurfaceInfoMacroTiled(
            tileMode,
            baseTileMode,
            bpp,
            numSamples,
            pitch,
            height,
            numSlices,
            mipLevel,
            padDims,
            flags)

    result = 0
    if valid == 0:
        result = 3

    pOut.pitch = pPitchOut
    pOut.height = pHeightOut
    pOut.depth = pNumSlicesOut
    pOut.tileMode = pTileModeOut
    pOut.surfSize = pSurfSize
    pOut.baseAlign = pBaseAlign
    pOut.pitchAlign = pPitchAlign
    pOut.heightAlign = pHeightAlign
    pOut.depthAlign = pDepthAlign

    return result


def restoreSurfaceInfo(elemMode, expandX, expandY, bpp):
    if bpp:
        if elemMode == 4:
            originalBits = expandY * expandX * bpp

        elif elemMode in [5, 6]:
            originalBits = bpp // expandX // expandY

        elif elemMode in [7, 8]:
            originalBits = bpp

        elif elemMode in [9, 12]:
            originalBits = 64

        elif elemMode in [10, 11, 13]:
            originalBits = 128

        elif elemMode in [0, 1, 2, 3]:
            originalBits = bpp

        else:
            originalBits = bpp

        bpp = originalBits

    if pOut.pixelPitch and pOut.pixelHeight:
        width = pOut.pixelPitch
        height = pOut.pixelHeight

        if expandX > 1 or expandY > 1:
            if elemMode == 4:
                width //= expandX
                height //= expandY

            else:
                width *= expandX
                height *= expandY

        pOut.pixelPitch = max(1, width)
        pOut.pixelHeight = max(1, height)

    return bpp


def computeSurfaceInfo(aSurfIn, pSurfOut):
    global pIn
    global pOut
    global ADDR_OK

    pIn = aSurfIn
    pOut = pSurfOut

    v4 = 0
    v6 = 0
    v7 = 0
    v8 = 0
    v10 = 0
    v11 = 0
    v12 = 0
    v18 = 0
    tileInfoNull = tileInfo()
    sliceFlags = 0

    returnCode = 0
    if getFillSizeFieldsFlags() == 1 and (pIn.size != 60 or pOut.size != 96):  # --> m_configFlags.value = 4
        returnCode = 6

    # v3 = pIn

    if pIn.bpp > 0x80:
        returnCode = 3

    if returnCode == ADDR_OK:
        v18 = 0

        computeMipLevel()

        width = pIn.width
        height = pIn.height
        bpp = pIn.bpp
        expandX = 1
        expandY = 1

        sliceFlags = getSliceComputingFlags()

        if useTileIndex(pIn.tileIndex) and pIn.pTileInfo is None:
            if pOut.pTileInfo is not None:
                pIn.pTileInfo = pOut.pTileInfo

            else:
                pOut.pTileInfo = tileInfoNull
                pIn.pTileInfo = tileInfoNull

        returnCode = 0  # does nothing
        if returnCode == ADDR_OK:
            pOut.pixelBits = pIn.bpp

            # v3 = pIn

            if pIn.format:
                v18 = 1
                v4 = pIn.format
                bpp, expandX, expandY, elemMode = getBitsPerPixel(v4)

                if elemMode == 4 and expandX == 3 and pIn.tileMode == 1:
                    pIn.flags.value |= 0x200

                v6 = expandY
                v7 = expandX
                v8 = elemMode
                bpp = adjustSurfaceInfo(v8, v7, v6, bpp, width, height)

            elif pIn.bpp:
                pIn.width = max(1, pIn.width)
                pIn.height = max(1, pIn.height)

            else:
                returnCode = 3

        if returnCode == ADDR_OK:
            returnCode = ComputeSurfaceInfoEx()

        if returnCode == ADDR_OK:
            pOut.bpp = pIn.bpp
            pOut.pixelPitch = pOut.pitch
            pOut.pixelHeight = pOut.height

            if pIn.format and (not ((pIn.flags.value >> 9) & 1) or not pIn.mipLevel):
                if not v18:
                    return

                v10 = expandY
                v11 = expandX
                v12 = elemMode
                bpp = restoreSurfaceInfo(v12, v11, v10, bpp)

            if sliceFlags:
                if sliceFlags == 1:
                    pOut.sliceSize = (pOut.height * pOut.pitch * pOut.bpp * pIn.numSamples + 7) // 8

            elif (pIn.flags.value >> 5) & 1:
                pOut.sliceSize = pOut.surfSize

            else:
                pOut.sliceSize = pOut.surfSize // pOut.depth

                if pIn.slice == (pIn.numSlices - 1) and pIn.numSlices > 1:
                    pOut.sliceSize += pOut.sliceSize * (pOut.depth - pIn.numSlices)

            pOut.pitchTileMax = (pOut.pitch >> 3) - 1
            pOut.heightTileMax = (pOut.height >> 3) - 1
            sliceTileMax = (pOut.height * pOut.pitch >> 6) - 1
            pOut.sliceTileMax = sliceTileMax


def getSurfaceInfo(surfaceFormat, surfaceWidth, surfaceHeight, surfaceDepth, surfaceDim, surfaceTileMode, surfaceAA, level):
    dim = 0
    width = 0
    blockSize = 0
    numSamples = 0
    hwFormat = 0

    aSurfIn = surfaceIn()
    pSurfOut = surfaceOut()

    hwFormat = surfaceFormat & 0x3F
    if surfaceTileMode == 16:
        numSamples = 1 << surfaceAA

        if hwFormat < 0x31 or hwFormat > 0x35:
            blockSize = 1

        else:
            blockSize = 4

        width = ~(blockSize - 1) & ((surfaceWidth >> level) + blockSize - 1)

        if hwFormat == 0x35:
            return pSurfOut

        pSurfOut.bpp = formatHwInfo[hwFormat * 4]
        pSurfOut.size = 96
        pSurfOut.pitch = width // blockSize
        pSurfOut.pixelBits = formatHwInfo[hwFormat * 4]
        pSurfOut.baseAlign = 1
        pSurfOut.pitchAlign = 1
        pSurfOut.heightAlign = 1
        pSurfOut.depthAlign = 1
        dim = surfaceDim

        if dim == 0:
            pSurfOut.height = 1
            pSurfOut.depth = 1

        elif dim == 1:
            pSurfOut.height = max(1, surfaceHeight >> level)
            pSurfOut.depth = 1

        elif dim == 2:
            pSurfOut.height = max(1, surfaceHeight >> level)
            pSurfOut.depth = max(1, surfaceDepth >> level)

        elif dim == 3:
            pSurfOut.height = max(1, surfaceHeight >> level)
            pSurfOut.depth = max(6, surfaceDepth)

        elif dim == 4:
            pSurfOut.height = 1
            pSurfOut.depth = surfaceDepth

        elif dim == 5:
            pSurfOut.height = max(1, surfaceHeight >> level)
            pSurfOut.depth = surfaceDepth

        pSurfOut.height = (~(blockSize - 1) & (pSurfOut.height + blockSize - 1)) // blockSize
        pSurfOut.pixelPitch = ~(blockSize - 1) & ((surfaceWidth >> level) + blockSize - 1)
        pSurfOut.pixelPitch = max(blockSize, pSurfOut.pixelPitch)
        pSurfOut.pixelHeight = ~(blockSize - 1) & ((surfaceHeight >> level) + blockSize - 1)
        pSurfOut.pixelHeight = max(blockSize, pSurfOut.pixelHeight)
        pSurfOut.pitch = max(1, pSurfOut.pitch)
        pSurfOut.height = max(1, pSurfOut.height)
        pSurfOut.surfSize = pSurfOut.bpp * numSamples * pSurfOut.depth * pSurfOut.height * pSurfOut.pitch >> 3

        if surfaceDim == 2:
            pSurfOut.sliceSize = pSurfOut.surfSize

        else:
            pSurfOut.sliceSize = pSurfOut.surfSize // pSurfOut.depth

        pSurfOut.pitchTileMax = (pSurfOut.pitch >> 3) - 1
        pSurfOut.heightTileMax = (pSurfOut.height >> 3) - 1
        pSurfOut.sliceTileMax = (pSurfOut.height * pSurfOut.pitch >> 6) - 1

    else:
        aSurfIn.size = 60
        aSurfIn.tileMode = surfaceTileMode & 0xF
        aSurfIn.format = hwFormat
        aSurfIn.bpp = formatHwInfo[hwFormat * 4]
        aSurfIn.numSamples = 1 << surfaceAA
        aSurfIn.numFrags = aSurfIn.numSamples
        aSurfIn.width = max(1, surfaceWidth >> level)
        dim = surfaceDim

        if dim == 0:
            aSurfIn.height = 1
            aSurfIn.numSlices = 1

        elif dim == 1:
            aSurfIn.height = max(1, surfaceHeight >> level)
            aSurfIn.numSlices = 1

        elif dim == 2:
            aSurfIn.height = max(1, surfaceHeight >> level)
            aSurfIn.numSlices = max(1, surfaceDepth >> level)

        elif dim == 3:
            aSurfIn.height = max(1, surfaceHeight >> level)
            aSurfIn.numSlices = max(6, surfaceDepth)
            aSurfIn.flags.value |= 0x10

        elif dim == 4:
            aSurfIn.height = 1
            aSurfIn.numSlices = surfaceDepth

        elif dim == 5:
            aSurfIn.height = max(1, surfaceHeight >> level)
            aSurfIn.numSlices = surfaceDepth

        elif dim == 6:
            aSurfIn.height = max(1, surfaceHeight >> level)
            aSurfIn.numSlices = 1

        elif dim == 7:
            aSurfIn.height = max(1, surfaceHeight >> level)
            aSurfIn.numSlices = surfaceDepth

        aSurfIn.slice = 0
        aSurfIn.mipLevel = level

        if surfaceDim == 2:
            aSurfIn.flags.value |= 0x20

        if level == 0:
            aSurfIn.flags.value = (1 << 12) | aSurfIn.flags.value & 0xFFFFEFFF

        else:
            aSurfIn.flags.value = aSurfIn.flags.value & 0xFFFFEFFF

        pSurfOut.size = 96
        computeSurfaceInfo(aSurfIn, pSurfOut)

        pSurfOut = pOut

    return pSurfOut

BCn_formats = [0x31, 0x431, 0x32, 0x432, 0x33, 0x433, 0x34, 0x234, 0x35, 0x235]

########################################################
########################################################



class ImportBFRES(Operator, ImportHelper):
    """Fills the current scene with the contents of the imported BFRES file."""
    bl_idname = "scene.import_bfres"
    bl_label = "Import BFRES"

    filename_ext = ".bfres"

    filter_glob = StringProperty(
            default="*.bfres",
            options={'HIDDEN'},
            maxlen=255,
            )
    @classmethod
    def poll(cls, context):
        return len(context.scene.objects) == 0
    
    def execute(self, context):
        context.scene.bfres.data = BFRES(self.filepath)
        if(context.scene.bfres.data.magic() != b'FRES'):
            self.report({'ERROR'}, "Not a BFRES file.")
            print("Error: Not a BFRES file.")
            return {'CANCELLED'}
        numTextures = context.scene.bfres.data.texture_index_group_count()
        print("Importing Textures...")
        for i in range(numTextures):
            ftex = context.scene.bfres.data.get_texture_data(i)
            tname = context.scene.bfres.data.get_texture_name(i)
            print("\tImporting Texture: %s\t\t%i of %i" % (tname, i+1, numTextures))
            if tname in bpy.data.images:
                bpy.data.images.remove(bpy.data.images[tname])
            
      ### FTEX DECODER BASED HEAVILY FROM BFRES-TOOL BY ABOODXD ###
      
            format_ = ftex.format()
            if ftex.num_bitmaps() > 14:
                self.report({'WARNING'}, "Number of mipmaps (%s) exceeded maximum (13) in model %s" % (str(ftex.num_bitmaps()-1), context.scene.bfres.data.get_model_name(i)))
                print("\tError: Number of mipmaps (%s) exceeded maximum (13) in model %s" % (str(ftex.num_bitmaps()-1), context.scene.bfres.data.get_model_name(i)))
                continue

            mipOffsets = []
            for i in range(13):
                mipOffsets.append(ftex.get_relative_mipmap_offset(i))

            compSelBytes = ftex.get_component_selector()
            compSel = []
            for i in range(4):
                comp = compSelBytes[i]
                if comp == 4: # Sorry, but this is unsupported.
                    comp = i
                compSel.append(comp)

            dataSize = ftex.data_length()
            mipSize = ftex.mipmap_data_length()
            data_pos = ftex.data_offset()
            mip_pos = ftex.mipmap_offset()

            data = bpy.context.scene.bfres.data.bytes[data_pos:data_pos+dataSize]

            if not (mip_pos and mipSize):
                mipData = b""
            else:
                mipData = bpy.context.scene.bfres.data.bytes[mip_pos:mip_pos+mipSize]

            numMips = ftex.num_bitmaps()
            width = ftex.width()
            height = ftex.height()
            depth = ftex.depth()
            dim = ftex.surface_dimension()
            aa = ftex.aa()
            tileMode = ftex.tile_mode()
            swizzle_ = ftex.swizzle_value()
            bpp = surfaceGetBitsPerPixel(format_) >> 3

            if format_ in BCn_formats:
                realSize = ((width + 3) >> 2) * ((height + 3) >> 2) * bpp
            else:
                realSize = width * height * bpp

            surfOut = getSurfaceInfo(format_, width, height, depth, dim, tileMode, aa, 0)

            if aa:
                self.report({'WARNING'}, "Unsupperted texture AA mode detected: %s in model %s" % (str(aa), context.scene.bfres.data.get_model_name(i)))
                print("\tError: Unsupperted texture AA mode detected: %s in model %s" % (str(aa), context.scene.bfres.data.get_model_name(i)))
                continue

            if surfOut.depth != 1:
                self.report({'WARNING'}, "Unsupperted texture depth detected: %s in model %s" % (str(surfOut.depth), context.scene.bfres.data.get_model_name(i)))
                print("\tError: Unsupperted texture depth detected: %s in model %s" % (str(surfOut.depth), context.scene.bfres.data.get_model_name(i)))
                continue

            result = []
            for level in range(numMips):
                if level != 0:
                    if level == 1:
                        mipOffset = mipOffsets[level - 1] - surfOut.surfSize
                    else:
                        mipOffset = mipOffsets[level - 1]

                    surfOut = getSurfaceInfo(format_, width, height, depth, dim, tileMode, aa, level)

                    data = mipData[mipOffset:mipOffset + surfOut.surfSize]
                deswizzled = deswizzle(max(1, width >> level), max(1, height >> level), surfOut.height, format_, surfOut.tileMode, swizzle_, surfOut.pitch, surfOut.bpp, data)

                if format_ in BCn_formats:
                    size = ((max(1, width >> level) + 3) >> 2) * ((max(1, height >> level) + 3) >> 2) * bpp
                else:
                    size = max(1, width >> level) * max(1, height >> level) * bpp
                
                rawdata = deswizzled[:size]
                
                if format_&0x1a == 0x1a: data = [rdb/255 for rdb in rawdata]
                elif format_&0x19 == 0x19:
                    data = [0 for i in range(width*height*4)]
                    pi = 0
                    for i in range(0, len(rawdata), 4):
                        rgb10a2 = struct.unpack("I", rawdata[i:i+4])[0]
                        data[pi] = (rgb10a2 & 0x3FF)/1023
                        data[pi+1] = ((rgb10a2 >> 10) & 0x3FF)/1023
                        data[pi+2] = ((rgb10a2 >> 20) & 0x3FF)/1023
                        data[pi+3] = ((rgb10a2 >> 30) & 0x3)/3
                        pi += 4
                elif format_ == 0xa:
                    data = [0 for i in range(width*height*4)]
                    pi = 0
                    for i in range(0, len(rawdata), 2):
                        rgb5a1 = struct.unpack("H", rawdata[i:i+2])[0]
                        data[pi] = ((rgb5a1 >> 11) & 0x1F)/31
                        data[pi+1] = ((rgb5a1 >> 6) & 0x1F)/31
                        data[pi+2] = ((rgb5a1 >> 1) & 0x1F)/31
                        data[pi+3] = (rgb5a1 & 0x1)
                        pi += 4
                elif format_ == 0xb:
                    data = [0 for i in range(width*height*4)]
                    pi = 0
                    for i in range(0, len(rawdata), 2):
                        rgba4 = struct.unpack("H", rawdata[i:i+2])[0]
                        data[pi] = ((rgba4) & 0xF)/15
                        data[pi+1] = ((rgba4 >> 4) & 0xF)/15
                        data[pi+2] = ((rgba4 >> 8) & 0xF)/15
                        data[pi+3] = ((rgba4 >> 12) & 0xF)/15
                        pi += 4
                elif format_ == 0x8:
                    data = [0 for i in range(width*height*4)]
                    pi = 0
                    for i in range(0, len(rawdata), 2):
                        r5g6b5 = struct.unpack("H", rawdata[i:i+2])[0]
                        data[pi] = ((r5g6b5) & 0x1F)/31
                        data[pi+1] = ((r5g6b5 >> 5) & 0x3F)/63
                        data[pi+2] = ((r5g6b5 >> 11) & 0x1F)/31
                        data[pi+3] = 1
                        pi += 4
                elif format_ == 0x107 or format_ == 0x7:
                    data = [0 for i in range(width*height*4)]
                    pi = 0
                    for i in range(0, len(rawdata), 2):
                        rg8 = rawdata[i:i+2]
                        data[pi] = rg8[0]/255
                        data[pi+1] = rg8[0]/255
                        data[pi+2] = rg8[0]/255
                        data[pi+3] = rg8[1]/255
                        pi += 4
                elif format_ == 0x1 or format_ == 0x101:
                    data = [0 for i in range(width*height*4)]
                    pi = 0
                    for i in range(len(rawdata)):
                        data[pi] = rawdata[i]/255
                        data[pi+1] = rawdata[i]/255
                        data[pi+2] = rawdata[i]/255
                        data[pi+3] = 1
                        pi += 4
                elif format_ == 0x31 or format_ == 0x431:
                    data = [0 for i in range(width*height*4)]
                    tx = ty = 0
                    for i in range(0, len(rawdata), 8):
                        rgbbits = struct.unpack("<2H", rawdata[i:i+4])
                        rgb1 = decode_rgb565(rgbbits[0])
                        rgb2 = decode_rgb565(rgbbits[1])
                        rgb_tween_bits = struct.unpack("<I", rawdata[i+4:i+8])[0]
                        x = y = 0
                        for j in range(16):
                            rgb_val = (rgb_tween_bits>>((j)*2))&0x3
                            a = 1
                            if rgbbits[0] <= rgbbits[1]:
                                if rgb_val == 0:
                                    tween = 0
                                elif rgb_val == 1:
                                    tween = 1
                                elif rgb_val == 2:
                                    tween = 1/2
                                elif rgb_val == 3:
                                    tween = 0
                                    a = 0
                            else:
                                if rgb_val == 0:
                                    tween = 0
                                elif rgb_val == 1:
                                    tween = 1
                                elif rgb_val == 2:
                                    tween = 1/3
                                elif rgb_val == 3:
                                    tween = 2/3
                            rgb = lerp_color(rgb1, rgb2, tween)
                            if (tx+x) < width and (ty+y) < height:
                                data[(((ty+y)*width)+(tx+x))*4:(((ty+y)*width)+(tx+x))*4+4] = [rgb[0], rgb[1], rgb[2], a]
                            
                            x+=1
                            if x >= 4:
                                x = 0
                                y+=1
                        tx+=4
                        if tx >= width:
                            tx=0
                            ty+=4
                elif format_ == 0x32 or format_ == 0x432:
                    data = [0 for i in range(width*height*4)]
                    tx = ty = 0
                    for i in range(0, len(rawdata), 16):
                        alphabits = struct.unpack(">Q", rawdata[i:i+8])[0]
                        rgbbits = struct.unpack("<2H", rawdata[i+8:i+12])
                        rgb1 = decode_rgb565(rgbbits[0])
                        rgb2 = decode_rgb565(rgbbits[1])
                        rgb_tween_bits = struct.unpack("<I", rawdata[i+12:i+16])[0]
                        x = y = 0
                        for j in range(16):
                            rgb_val = (rgb_tween_bits>>((j)*2))&0x3
                            a = ((alphabits>>((15-j)*4))&0xF)/15
                            if rgb_val == 0:
                                tween = 0
                            elif rgb_val == 1:
                                tween = 1
                            elif rgb_val == 2:
                                tween = 1/3
                            elif rgb_val == 3:
                                tween = 2/3
                            rgb = lerp_color(rgb1, rgb2, tween)
                            if (tx+x) < width and (ty+y) < height:
                                data[(((ty+y)*width)+(tx+x))*4:(((ty+y)*width)+(tx+x))*4+4] = [rgb[0], rgb[1], rgb[2], a]
                            
                            x+=1
                            if x >= 4:
                                x = 0
                                y+=1
                        tx+=4
                        if tx >= width:
                            tx=0
                            ty+=4
                elif format_ == 0x33 or format_ == 0x433:
                    data = [0 for i in range(width*height*4)]
                    tx = ty = 0
                    for i in range(0, len(rawdata), 16):
                        a1 = rawdata[i]/255
                        a2 = rawdata[i+1]/255
                        alpha_tween_bits = struct.unpack("Q", rawdata[i:i+8])[0] >> 16
                        rgbbits = struct.unpack("<2H", rawdata[i+8:i+0xC])
                        rgb1 = decode_rgb565(rgbbits[0])
                        rgb2 = decode_rgb565(rgbbits[1])
                        rgb_tween_bits = struct.unpack("<I", rawdata[i+0xC:i+0x10])[0]
                        x = y = 0
                        for j in range(16):
                            rgb_val = (rgb_tween_bits>>((j)*2))&0x3
                            if rgb_val == 0:
                                tween = 0
                            elif rgb_val == 1:
                                tween = 1
                            elif rgb_val == 2:
                                tween = 1/3
                            elif rgb_val == 3:
                                tween = 2/3
                            rgb = lerp_color(rgb1, rgb2, tween)
                            a_val = (alpha_tween_bits>>((j)*3))&0x7
                            if a_val == 0:
                                value = a1
                            elif a_val == 1:
                                value = a2
                            elif a_val == 2:
                                value = a1+(a2-a1)*(1/7)
                            elif a_val == 3:
                                value = a1+(a2-a1)*(2/7)
                            elif a_val == 4:
                                value = a1+(a2-a1)*(3/7)
                            elif a_val == 5:
                                value = a1+(a2-a1)*(4/7)
                            elif a_val == 6:
                                value = 0 if (a2 - a1) < 2 and (a2 - a1) >= 0 else a1+(a2-a1)*(5/7)
                            elif a_val == 7:
                                value = 1 if (a2 - a1) < 2 and (a2 - a1) >= 0 else a1+(a2-a1)*(6/7)
                                
                            if (tx+x) < width and (ty+y) < height:
                                data[(((ty+y)*width)+(tx+x))*4:(((ty+y)*width)+(tx+x))*4+4] = [rgb[0], rgb[1], rgb[2], value]
                                
                            x+=1
                            if x >= 4:
                                x = 0
                                y+=1
                        tx+=4 
                        if tx >= width:
                            tx=0
                            ty+=4
                elif format_ == 0x34 or format_ == 0x234:
                    data = [0 for i in range(width*height*4)]
                    tx = ty = 0
                    for i in range(0, len(rawdata), 8):
                        if format_&0x200:
                            b1, b2 = rawdata[i:i+2]
                            b1+=0x80
                            if b1 >= 0x100: b1 -= 0x100
                            b2+=0x80
                            if b2 >= 0x100: b2 -= 0x100
                            v1 = b1/255
                            v2 = b2/255
                        else:
                            v1 = rawdata[i]/255
                            v2 = rawdata[i+1]/255
                        value_tween_bits = struct.unpack("Q", rawdata[i:i+8])[0] >> 16
                        x = y = 0
                        for j in range(16):
                            val = (value_tween_bits>>((j)*3))&0x7
                            if val == 0:
                                value = v1
                            elif val == 1:
                                value = v2
                            elif val == 2:
                                value = v1+(v2-v1)*(1/7)
                            elif val == 3:
                                value = v1+(v2-v1)*(2/7)
                            elif val == 4:
                                value = v1+(v2-v1)*(3/7)
                            elif val == 5:
                                value = v1+(v2-v1)*(4/7)
                            elif val == 6:
                                value = 0 if (v2 - v1) < 2 and (v2 - v1) >= 0 else v1+(v2-v1)*(5/7)
                            elif val == 7:
                                value = 1 if (v2 - v1) < 2 and (v2 - v1) >= 0 else v1+(v2-v1)*(6/7)
                                
                            if (tx+x) < width and (ty+y) < height:
                                data[(((ty+y)*width)+(tx+x))*4:(((ty+y)*width)+(tx+x))*4+4] = [value, value, value, 1]
                                
                            x+=1
                            if x >= 4:
                                x = 0
                                y+=1
                        tx+=4 
                        if tx >= width:
                            tx=0
                            ty+=4
                elif format_ == 0x35 or format_ == 0x235:
                    data = [0 for i in range(width*height*4)]
                    tx = ty = 0
                    for i in range(0, len(rawdata), 16):
                        if format_&0x200:
                            xb1, xb2 = rawdata[i:i+2]
                            xb1+=0x80
                            if xb1 >= 0x100: xb1 -= 0x100
                            xb2+=0x80
                            if xb2 >= 0x100: xb2 -= 0x100
                            yb1, yb2 = rawdata[i+8:i+10]
                            yb1+=0x80
                            if yb1 >= 0x100: yb1 -= 0x100
                            yb2+=0x80
                            if yb2 >= 0x100: yb2 -= 0x100
                            xv1 = xb1/255
                            xv2 = xb2/255
                            yv1 = yb1/255
                            yv2 = yb2/255
                        else:
                            xv1 = rawdata[i]/255
                            xv2 = rawdata[i+1]/255
                            yv1 = rawdata[i+8]/255
                            yv2 = rawdata[i+9]/255
                        x_value_tween_bits = struct.unpack("Q", rawdata[i:i+8])[0] >> 16
                        
                        y_value_tween_bits = struct.unpack("Q", rawdata[i+8:i+16])[0] >> 16
                        
                        x = y = 0
                        for j in range(16):
                            x_val = (x_value_tween_bits>>((j)*3))&0x7
                            if x_val == 0:
                                x_value = xv1
                            elif x_val == 1:
                                x_value = xv2
                            elif x_val == 2:
                                x_value = xv1+(xv2-xv1)*(1/7)
                            elif x_val == 3:
                                x_value = xv1+(xv2-xv1)*(2/7)
                            elif x_val == 4:
                                x_value = xv1+(xv2-xv1)*(3/7)
                            elif x_val == 5:
                                x_value = xv1+(xv2-xv1)*(4/7)
                            elif x_val == 6:
                                x_value = 0 if (xv2 - xv1) < 2 and (xv2 - xv1) >= 0 else xv1+(xv2-xv1)*(5/7)
                            elif x_val == 7:
                                x_value = 1 if (xv2 - xv1) < 2 and (xv2 - xv1) >= 0 else xv1+(xv2-xv1)*(6/7)
                                
                            y_val = (y_value_tween_bits>>((j)*3))&0x7
                            if y_val == 0:
                                y_value = yv1
                            elif y_val == 1:
                                y_value = yv2
                            elif y_val == 2:
                                y_value = yv1+(yv2-yv1)*(1/7)
                            elif y_val == 3:
                                y_value = yv1+(yv2-yv1)*(2/7)
                            elif y_val == 4:
                                y_value = yv1+(yv2-yv1)*(3/7)
                            elif y_val == 5:
                                y_value = yv1+(yv2-yv1)*(4/7)
                            elif y_val == 6:
                                y_value = 0 if (yv2 - yv1) < 2 and (yv2 - yv1) >= 0 else yv1+(yv2-yv1)*(5/7)
                            elif y_val == 7:
                                y_value = 1 if (yv2 - yv1) < 2 and (yv2 - yv1) >= 0 else yv1+(yv2-yv1)*(6/7)
                                
                            if (tx+x) < width and (ty+y) < height:
                                data[(((ty+y)*width)+(tx+x))*4:(((ty+y)*width)+(tx+x))*4+4] = [x_value, y_value, 1, 1]
                                
                            x+=1
                            if x >= 4:
                                x = 0
                                y+=1
                        tx+=4 
                        if tx >= width:
                            tx=0
                            ty+=4
                else: result = None; break
                                
                result.append(data)
            if result == None:
                self.report({'WARNING'}, "Unrecognized texture format detected: %s in model %s" % (ftex.format_string(), context.scene.bfres.data.get_model_name(i)))
                print("\tError: Unrecognized texture format detected: %s in model %s" % (ftex.format_string(), context.scene.bfres.data.get_model_name(i)))
                continue
            img = bpy.data.images.new(tname, width, height, alpha=True)
            img.use_alpha = True
            img.alpha_mode = 'STRAIGHT'
            img.filepath = bpy.context.user_preferences.filepaths.temporary_directory+tname+".tga"
            img.file_format = 'TARGA'
            pixels = [0 for i in range(width*height*4)]
            i = 0
            for y in range(height-1, -1, -1):
                for x in range(width):
                    pixels[(y*width+x)*4:(y*width+x)*4+4] = result[0][i:i+4]
                    i+=4
            img.pixels[:] = pixels
            img.save()
            img.pack()

        print("Importing Models...")
        numModels = context.scene.bfres.data.model_index_group_count()
        for i in range(numModels):
            fmdl = context.scene.bfres.data.get_model_data(i)
            fmdlname = context.scene.bfres.data.get_model_name(i)
            print("\tImporting Model: %s\t\t%i of %i" % (fmdlname, i+1, numModels))
            #Importing Skeleton
            
            skl = fmdl.get_skeleton_data()
            arm = bpy.data.objects.new(context.scene.bfres.data.get_model_name(i)+"_armature", bpy.data.armatures.new(context.scene.bfres.data.get_model_name(i)+"_armature"))
            
            context.scene.objects.link(arm)
            context.scene.objects.active = arm
            bpy.ops.object.mode_set(mode='EDIT')
            print("\t\tImporting Bones...")
            numBones = skl.num_bones()
            for k in range(numBones):
                bn = arm.data.edit_bones.new(skl.get_bone_name(k))
                print("\t\t\tImporting Bone: %s\t\t%i of %i" % (bn, k+1, numBones))
                src_bn = skl.get_bone_data(k)
                pos = src_bn.translation_vector()
                rot = src_bn.rotation_vector()
                scl = src_bn.scale_vector()
                bn.tail = bn.head + Vector((0,0,1))
                bn.matrix = matrix_from_transform(Vector((pos[0], pos[1], pos[2])), Euler(((rot[0]), (rot[1]), (rot[2]))) if src_bn.uses_euler() else Quaternion((rot[3], rot[0], rot[1], rot[2])), (scl[0], scl[1], scl[2]))
                pb = skl.get_bone_data(src_bn.parent_index())
                while pb is not None:
                    pos = pb.translation_vector()
                    rot = pb.rotation_vector()
                    scl = pb.scale_vector()
                    bn.matrix = flipMtx(flipMtx(bn.matrix) * flipMtx(matrix_from_transform(Vector((pos[0], pos[1], pos[2])),  Euler(((rot[0]), (rot[1]), (rot[2]))) if pb.uses_euler() else Quaternion((rot[3], rot[0], rot[1], rot[2])), (scl[0], scl[1], scl[2]))))
                    pb = skl.get_bone_data(pb.parent_index())
                bn.matrix = flipYZ*bn.matrix
            
            print("\t\tParenting Bones...")
            for k in range(numBones):
                bn = arm.data.edit_bones[skl.get_bone_name(k)]
                src_bn = skl.get_bone_data(k)
                pi = src_bn.parent_index()
                if skl.get_bone_name(pi) is not None: bn.parent = arm.data.edit_bones[skl.get_bone_name(pi)]
            bpy.ops.object.mode_set(mode='OBJECT')                
            
            print("\t\tImporting Vertex Buffers...")
            #Importing Models
            
            bm = bmesh.new()
            _pcs = [0]
            ns = []
            uvls = []
            wis = []
            whts = []
            for nv in range(fmdl.total_num_vertices()):
                bm.verts.new()
                uvls.append((0,0))
                ns.append((0,0,0))
                wis.append(None)
                whts.append(None)
            bm.verts.ensure_lookup_table()
            
            _vseek = 0
            numPolys = fmdl.get_polygon_count()
            for j in range(numPolys):
                print("\t\t\tImporting Vertex Buffer: %i of %i" % (j+1, numPolys))
                s = fmdl.get_polygon_data(j)
                v = FVTX(s.vertex_offset(), fmdl, context.scene.bfres.data)
                _uvbuffer = False
                for k in range(v.attribute_count()):
                    va = v.get_attribute_data(k)
                    name = v.get_attribute_name(k)
                    if name == "_p0": None
                    elif name == "_n0": None
                    elif name == "_u0":
                        if _uvbuffer: continue
                        else: _uvbuffer = True
                    elif name == "_i0":
                        None
                    elif name == "_w0":
                        None
                    else: continue
                    fmt = va.format_string()
                    bo = v.get_buffer_offset(va.buffer_index())+va.buffer_offset()
                    vd = []
                    stride = v.get_buffer_stride(va.buffer_index())
                    size = v.get_buffer_size(va.buffer_index())
                                        
                    for o in range(bo, bo+size, stride):
                        if fmt == "float_32_32_32":
                            vd.append(struct.unpack(">3f", context.scene.bfres.data.bytes[o:o+0xC]))
                        elif fmt == "float_16_16_16_16":
                            vd.append(numpy.frombuffer(context.scene.bfres.data.bytes[o:o+0x8 ], dtype=">4f2")[0].tolist())
                        elif fmt == "snorm_16_16":
                            val = numpy.frombuffer(context.scene.bfres.data.bytes[o:o+0x4 ], dtype=">2h")[0].tolist()
                            val[0]/=0x7FFF
                            val[1]/=0x7FFF
                            vd.append(val)
                        elif fmt == "unorm_16_16":
                            val = numpy.frombuffer(context.scene.bfres.data.bytes[o:o+0x4 ], dtype=">2H")[0].tolist()
                            val[0]/=0xFFFF
                            val[1]/=0xFFFF
                            vd.append(val)
                        elif fmt == "float_32_32":
                            vd.append(numpy.frombuffer(context.scene.bfres.data.bytes[o:o+0x8 ], dtype=">2f")[0].tolist())
                        elif fmt == "float_16_16":
                            vd.append(numpy.frombuffer(context.scene.bfres.data.bytes[o:o+0x4 ], dtype=">2f2")[0].tolist())
                        elif fmt == "snorm_10_10_10_2":
                            vd.append(_parse_3x_10bit_signed(context.scene.bfres.data.bytes, o))
                        elif fmt == "uint_8":
                            vd.append((context.scene.bfres.data.bytes[o],))
                        elif fmt == "uint_8_8":
                            vd.append((context.scene.bfres.data.bytes[o],context.scene.bfres.data.bytes[o+1]))
                        elif fmt == "uint_8_8_8_8":
                            vd.append((context.scene.bfres.data.bytes[o],context.scene.bfres.data.bytes[o+1],context.scene.bfres.data.bytes[o+2],context.scene.bfres.data.bytes[o+3]))
                        elif fmt == "unorm_8_8":
                            vd.append((context.scene.bfres.data.bytes[o]/255.0,context.scene.bfres.data.bytes[o+1]/255.0))
                        elif fmt == "snorm_8_8":
                            vd.append((context.scene.bfres.data.bytes[o]/255.0,context.scene.bfres.data.bytes[o+1]/255.0))
                        elif fmt == "unorm_8_8_8_8":
                            vd.append((context.scene.bfres.data.bytes[o]/255.0,context.scene.bfres.data.bytes[o+1]/255.0,context.scene.bfres.data.bytes[o+2]/255.0,context.scene.bfres.data.bytes[o+3]/255.0))
                        else:
                            self.report({'WARNING'}, "Unrecognized buffer format detected: %s in model %s" % (fmt, context.scene.bfres.data.get_model_name(i)))
                            print("\t\t\tError: Unrecognized buffer format detected: %s in model %s" % (fmt, context.scene.bfres.data.get_model_name(i)))
                            break
                    if v.get_attribute_name(k) == "_p0":
                        vi = 0
                        for vtx in vd:
                            while len(vtx) < 3:
                                vtx.append(0)
                            _vseek = vi+_pcs[j]
                            bm.verts[_vseek].co = (vtx[0], vtx[1], vtx[2])
                            vi+=1
                    if v.get_attribute_name(k) == "_n0":
                        ni = 0
                        for nml in vd:
                            while len(nml) < 3:
                                nml.append(0)
                            ns[ni + _pcs[j]] = (nml[2],nml[1],nml[0])
                            bm.verts[ni+_pcs[j]].normal = (nml[2],nml[1],nml[0])
                            ni+=1
                    if v.get_attribute_name(k) == "_u0":
                        ui = 0
                        for uv in vd:
                            while len(uv) < 2:
                                uv.append(0)
                            uvls[ui + _pcs[j]] = (uv[0], 1-uv[1])
                            ui += 1
                    if v.get_attribute_name(k) == "_i0":
                        wi = 0
                        for wv in vd:
                            wis[wi + _pcs[j]] = wv
                            wi += 1
                    if v.get_attribute_name(k) == "_w0":
                        whi = 0
                        for whv in vd:
                            whts[whi + _pcs[j]] = whv
                            whi += 1
                _pcs.append(_vseek+1)
            mi = []
            pmi = []
            print("\t\tImporting Polygons...")
            for j in range(numPolys):
                print("\t\t\tImporting Polygon: %i of %i" % (j+1, numPolys))
                s = fmdl.get_polygon_data(j)
                lod = s.get_LoD_model(0)
                pt = lod.primitive_type_string()
                i_f = lod.index_format_string()
                bo = lod.get_buffer_offset()
                id = []
                size = lod.get_buffer_size()
                o = bo
                while o < bo+size:
                    if i_f == "GX2_INDEX_FORMAT_U16":
                        id.append(struct.unpack(">H", context.scene.bfres.data.bytes[o:o+2])[0])
                        o+=2
                    else:
                        self.report({'WARNING'}, "Unrecognized index format detected: %s in model %s" % (i_f, context.scene.bfres.data.get_model_name(i)))
                        print("\t\t\tError: Unrecognized index format detected: %s in model %s" % (i_f, context.scene.bfres.data.get_model_name(i)))
                        break
                _tri = []
                for index in id:
                    if pt == "GX2_PRIMITIVE_TRIANGLES":
                        _tri.append(index)
                        if len(_tri) == 3:
                            try:
                                face = bm.faces.new((bm.verts[_tri[0]+_pcs[j]],bm.verts[_tri[1]+_pcs[j]],bm.verts[_tri[2]+_pcs[j]]))
                                face.smooth = True
                                mi.append(j)
                            except:
                                None
                            _tri = []
                    else:
                        self.report({'WARNING'}, "Unrecognized primitive type detected: %s in model %s" % (pt, context.scene.bfres.data.get_model_name(i)))
                        print("\t\t\tError: Unrecognized primitive type detected: %s in model %s" % (pt, context.scene.bfres.data.get_model_name(i)))
                        break
                pmi.append(s.material_index())
            
            bm.faces.ensure_lookup_table()
                                
            m = bpy.data.meshes.new(fmdlname)
            
            bm.to_mesh(m)
            
            uvtt = m.uv_textures.new("Map")
            uvtl = m.uv_layers["Map"]
            for p in m.polygons:
                for vi in range(len(p.loop_indices)):
                    uvtl.data[p.loop_indices[vi]].uv = uvls[p.vertices[vi]]
            
            
            #Importing Materials
            print("\t\tImporting Materials...")
            mats = []
            numMaterials = fmdl.get_material_count()
            for mt in range(numMaterials):
                inmat = fmdl.get_material_data(mt)
                mname = fmdlname+"/"+fmdl.get_material_name(mt)
                print("\t\t\tImporting Material: %s\t\t%i of %i" % (mname, mt+1, numMaterials))
                if mname in bpy.data.materials:
                    bpy.data.materials.remove(bpy.data.materials[mname])
                outmat = bpy.data.materials.new(mname)
                if context.scene.render.engine == "CYCLES":
                    outmat.use_nodes = True
                    nt = outmat.node_tree
                    for tpi in range(inmat.texture_param_count()):
                        tpname = inmat.get_texture_param_name(tpi)
                        tp = inmat.get_texture_param_data(tpi)
                        index = tp.index()
                        if tpname == "_a0":
                            img_node = nt.nodes.new('ShaderNodeTexImage')
                            img_node.image = bpy.data.images[inmat.get_texture_name(index)]
                            nt.links.new(img_node.outputs[0], nt.nodes["Diffuse BSDF"].inputs[0])
                            mix_shader_node = nt.nodes.new('ShaderNodeMixShader')
                            transparent_shader_node = nt.nodes.new('ShaderNodeBsdfTransparent')
                            nt.links.new(img_node.outputs[1], mix_shader_node.inputs[0])
                            nt.links.new(transparent_shader_node.outputs[0], mix_shader_node.inputs[1])
                            nt.links.new(nt.nodes["Diffuse BSDF"].outputs[0], mix_shader_node.inputs[2])
                            nt.links.new(mix_shader_node.outputs[0], nt.nodes["Material Output"].inputs[0])
                else:
                    outmat.diffuse_color.s = random()*0.5+0.5
                    outmat.diffuse_color.v = random()*0.125+0.875
                    h = random()
                    outmat.diffuse_color.h = h
                    for tpi in range(inmat.texture_param_count()):
                        tpname = inmat.get_texture_param_name(tpi)
                        tp = inmat.get_texture_param_data(tpi)
                        index = tp.index()
                        img = bpy.data.images[inmat.get_texture_name(index)]
                        ts = outmat.texture_slots.add()
                        ts.texture = bpy.data.textures.new(mname+"/"+img.name, 'IMAGE')
                        ts.texture.image = img
                mats.append(outmat)
                
            for pmii in pmi:
                m.materials.append(mats[pmii])
            
            
            for pi in range(len(m.polygons)):
                m.polygons[pi].material_index = mi[pi]
                if m.materials[mi[pi]].texture_slots[0] is not None:
                    uvtt.data[pi].image = m.materials[mi[pi]].texture_slots[0].texture.image
            #vc = m.vertex_colors.new("normTest")
            #v = 0
            #for t in bm.faces:
            #    for l in t.loops:
            #        vc.data[v].color[0] = l.vert.normal[0]
            #        vc.data[v].color[1] = l.vert.normal[1]
            #        vc.data[v].color[2] = l.vert.normal[2]
            #        v+=1
            
            
            o = bpy.data.objects.new(fmdlname, m)
            for k in range(numBones): o.vertex_groups.new(skl.get_bone_name(k))
            o.modifiers.new("SKL_bind", 'ARMATURE').object = arm
            
            print("\t\tBinding Vertices to Bones...")
            for iii in range(_pcs[len(_pcs)-1]):
                iik = 0
                for iij in range(1, len(_pcs)):
                    if iii >= _pcs[iij-1] and iii < _pcs[iij]:
                        break
                    iik+=1
                s = fmdl.get_polygon_data(iik)
                sm = s.vertex_skin_count()
                if sm == 0:
                    bone_index = s.skeleton_index()
                    bname = skl.get_bone_name(bone_index, True)
                    context.scene.objects.active = arm
                    o.vertex_groups[bname].add((iii,), 1, 'ADD')
                    bpy.ops.object.mode_set(mode='EDIT')
                    mtx = arm.data.edit_bones[bname].matrix
                    bpy.ops.object.mode_set(mode='OBJECT')
                    m.vertices[iii].co = mtx*m.vertices[iii].co
                    m.vertices[iii].normal = mtx.to_3x3()*m.vertices[iii].normal
                    ns[iii] = (mtx.to_3x3()*Vector(ns[iii])).to_tuple()
                if sm == 1:
                    bone_index = skl.get_smooth_index(wis[iii][0])
                    bname = skl.get_bone_name(bone_index)
                    o.vertex_groups[bname].add((iii,), 1, 'ADD')
                    bpy.ops.object.mode_set(mode='EDIT')
                    mtx = arm.data.edit_bones[bname].matrix
                    bpy.ops.object.mode_set(mode='OBJECT')
                    m.vertices[iii].co = mtx*m.vertices[iii].co
                    m.vertices[iii].normal = mtx.to_3x3()*m.vertices[iii].normal
                    ns[iii] = (mtx.to_3x3()*Vector(ns[iii])).to_tuple()
                if sm >= 2:
                    for w in range(sm):
                        bone_index = skl.get_smooth_index(wis[iii][w])
                        bname = skl.get_bone_name(bone_index)
                        o.vertex_groups[bname].add((iii,), whts[iii][w], 'ADD')
                    m.vertices[iii].co = flipYZ*m.vertices[iii].co
                    m.vertices[iii].normal = flipYZ.to_3x3()*m.vertices[iii].normal
                    ns[iii] = (flipYZ.to_3x3()*Vector(ns[iii])).to_tuple()
            
            print("\t\tFinalizing Model...")
            m.use_auto_smooth = True
            nms = []
            for n in ns:
                nms.append(Vector(n).normalized())
            
            m.normals_split_custom_set_from_vertices(nms)
            
            context.scene.objects.link(o)
                
        return {'FINISHED'}


class View3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

class BFRESImporter(View3DPanel, bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "BFRES Importer"
    bl_idname = "OBJECT_PT_BFRES"
    bl_category = "BFRES"
    bl_context = "objectmode"
    bl_label = "Import BFRES"

    def draw(self, context):
        layout = self.layout

        obj = context.object
        
        if len(context.scene.objects) != 0:
            row = layout.row()
            row.label("This scene must be empty.", icon='INFO')
        row = layout.row()
        row.operator("scene.import_bfres")


def register():
    bpy.types.Scene.bfres = BFRESslot
    bpy.utils.register_class(ImportBFRES)
    bpy.utils.register_class(BFRESImporter)


def unregister():
    bpy.utils.unregister_class(ImportBFRES)
    bpy.utils.unregister_class(BFRESImporter)


if __name__ == "__main__":
    register()
