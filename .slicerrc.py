import numpy as np
from scipy import ndimage
import vtkITK
import random

def init():
  for node in getNodesByClass('vtkMRMLSliceCompositeNode'):
    node.SetLinkedControl(1)
  
  # create custom colormap, end init if exists  
  if len(getNodes('custom_color')) > 0:
    return
  
  segment_names_to_labels = [("bg", 0), ("c", 1), ("s", 2), ("h0", 3), ("h1", 4), ("h2", 5), ("h3", 6), ("h4", 7), ("h5", 8), ("h6", 9), ("h7", 10),
                             ("b0", 11), ("b1", 12), ("b2", 13), ("b3", 14), ("b4", 15), ("b5", 16), ("h_unif", 17), ("b_unif", 18)]
  
  
  colorTableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLColorTableNode","custom_color")
  colorTableNode.SetTypeToUser()
  colorTableNode.HideFromEditorsOff()  # make the color table selectable in the GUI outside Colors module
  slicer.mrmlScene.AddNode(colorTableNode); colorTableNode.UnRegister(None)
  colorTableNode.SetNumberOfColors(19)
  colorTableNode.SetNamesInitialised(True) # prevent automatic color name generation
  
  random.seed(1) #deterministic random values
  for segmentName, labelValue in segment_names_to_labels:
    if labelValue == 0:
      r,g,b,a = 0,0,0,0
    else:
      r = random.uniform(0.0, 1.0)
      g = random.uniform(0.0, 1.0)
      b = random.uniform(0.0, 1.0)
      a = 0.4    
    success = colorTableNode.SetColor(labelValue, segmentName, r, g, b, a)

# locate orientation fiducials
def locate():
  z_axis = 0
  volNode = getNode(slicer.app.applicationLogic().GetSliceLogic(slicer.app.layoutManager().sliceWidget("Red").mrmlSliceNode()).GetSliceCompositeNode().GetBackgroundVolumeID())
  vol = slicer.util.arrayFromVolume(volNode)
  l,n = ndimage.label(np.median(vol,axis=z_axis) > -500)
  mask = (l == (np.argmax([np.sum(l == i) for i in range(1,n+1)])+1))
  ring = ndimage.binary_dilation(mask,np.ones((20,20))) & (ndimage.binary_erosion(mask,np.ones((20,20))) == False)
  ring = np.repeat(np.expand_dims(ring,axis=z_axis), vol.shape[z_axis], axis=z_axis)
  out = (vol > 400) & ring
  z = np.median(np.where(np.max(out,axis=(1,2))))
  
  mat=vtk.vtkMatrix4x4()
  volNode.GetIJKToRASMatrix(mat)
  K = round(mat.MultiplyPoint([0,0,z,1])[2])
  slicer.app.layoutManager().sliceWidget("Red").mrmlSliceNode().SetSliceOffset(K)

# detect phantom edges and use assumed locations for inserts
def detect():
  volNode = getNode(slicer.app.applicationLogic().GetSliceLogic(slicer.app.layoutManager().sliceWidget("Red").mrmlSliceNode()).GetSliceCompositeNode().GetBackgroundVolumeID())
  tmp = slicer.util.getNodes('inserts-label')
  if len(tmp) > 0:
    labelNode = tmp.popitem(last=False)[1]
  else:
    labelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode",'inserts-label')
    slicer.vtkSlicerVolumesLogic().CreateLabelVolumeFromVolume(slicer.mrmlScene, labelNode, volNode)
    slicer.util.updateVolumeFromArray(labelNode, (slicer.util.arrayFromVolume(labelNode) * 0).astype("int8"))
    labelNode.GetDisplayNode().SetAndObserveColorNodeID(getNode('custom_color').GetID())
  for col in ("Red","Green","Yellow"):
    slicer.app.applicationLogic().GetSliceLogic(slicer.app.layoutManager().sliceWidget(col).mrmlSliceNode()).GetSliceCompositeNode().SetLabelVolumeID(labelNode.GetID())
  
  for node in getNodesByClass('vtkMRMLMarkupsFiducialNode'):
    slicer.mrmlScene.RemoveNode(node)
  sliceNode = slicer.app.layoutManager().sliceWidget("Red").mrmlSliceNode()
  offset = sliceNode.GetSliceOffset()
  mat=vtk.vtkMatrix4x4()
  volNode.GetRASToIJKMatrix(mat)
  mat_ijk=vtk.vtkMatrix4x4()
  volNode.GetIJKToRASMatrix(mat_ijk)
  K = round(mat.MultiplyPoint([0,0,offset,1])[2])
  vol = slicer.util.arrayFromVolume(volNode)
  slice = vol[K,:,:]
  l,n = ndimage.label(slice > -500)
  mask = l == (np.argmax([np.sum(l == i) for i in range(1,n)])+1)
  tmp=np.where(np.sum(mask,axis=0)); x_ind = tmp[0][0],tmp[0][-1]
  x0 = int(np.round((x_ind[0]+x_ind[1])/2))
  tmp=np.where(mask[:,x0]>0); y_ind = tmp[0][0],tmp[0][-1]; y_ind
  y0 = int(np.round((y_ind[0]+y_ind[1])/2))
  center_point_ras = list(mat_ijk.MultiplyPoint([x0,y0,K,1])[0:2])+[offset]
  pointListNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode",'head_inserts')
  pointListNode.GetDisplayNode().SetSliceProjection(1)
  _=pointListNode.AddControlPoint(center_point_ras,'c')
  R = 75 # head inserts are 75 mm from the center
  S=2**0.5
  r0,a0,s0 = center_point_ras
  _=pointListNode.AddControlPoint([r0-R,a0,s0],'h0')
  _=pointListNode.AddControlPoint([r0-R/S,a0+R/S,s0],'h1')
  _=pointListNode.AddControlPoint([r0,a0+R,s0],'h2')
  _=pointListNode.AddControlPoint([r0+R/S,a0+R/S,s0],'h3')
  _=pointListNode.AddControlPoint([r0+R,a0,s0],'h4')
  _=pointListNode.AddControlPoint([r0+R/S,a0-R/S,s0],'h5')
  _=pointListNode.AddControlPoint([r0,a0-R,s0],'h6')
  _=pointListNode.AddControlPoint([r0-R/S,a0-R/S,s0],'h7')
  for N in range(pointListNode.GetNumberOfControlPoints()):
    pointListNode.SetNthControlPointDescription(N,"10")
    
  pointListNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode",'head_special_insert')
  pointListNode.GetDisplayNode().SetSliceProjection(1)
  _=pointListNode.AddControlPoint([r0,a0-R/2,s0],'s')
  for N in range(pointListNode.GetNumberOfControlPoints()):
    pointListNode.SetNthControlPointDescription(N,"10")
  
  pointListNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode",'body_inserts')
  pointListNode.GetDisplayNode().SetSliceProjection(1)
  R = 140 # body inserts are 14 cm from the center
  r0,a0,s0 = center_point_ras
  _=pointListNode.AddControlPoint([r0-R,a0,s0],'b0')
  _=pointListNode.AddControlPoint([r0-R/S,a0+R/S,s0],'b1')
  _=pointListNode.AddControlPoint([r0+R/S,a0+R/S,s0],'b2')
  _=pointListNode.AddControlPoint([r0+R,a0,s0],'b3')
  _=pointListNode.AddControlPoint([r0+R/S,a0-R/S,s0],'b4')
  _=pointListNode.AddControlPoint([r0-R/S,a0-R/S,s0],'b5')
  for N in range(pointListNode.GetNumberOfControlPoints()):
    pointListNode.SetNthControlPointDescription(N,"10")
  
  for node in getNodes('*_tf').values():
    slicer.mrmlScene.RemoveNode(node)
  forward_tf               = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode",'__forward_tf')
  backward_body_tf         = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode",'__backward_body_tf')
  backward_head_tf         = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode",'__backward_head_tf')
  backward_head_special_tf = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode",'__backward_head_special_tf')
  for f,tf in zip((-1,1,1,1),(forward_tf,backward_body_tf,backward_head_tf,backward_head_special_tf)):
    m = tf.GetMatrixTransformFromParent()
    m.SetElement(1,3,f*center_point_ras[1])
    tf.SetMatrixTransformFromParent(m)
  phantom_tf      = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode",'phantom_tf')
  head_tf         = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode",'head_tf')
  head_special_tf = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode",'head_special_tf')
  body_tf         = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode",'body_tf') 
  head_tf.SetAndObserveTransformNodeID(phantom_tf.GetID())
  head_special_tf.SetAndObserveTransformNodeID(head_tf.GetID())
  body_tf.SetAndObserveTransformNodeID(phantom_tf.GetID())
  phantom_tf.SetAndObserveTransformNodeID(forward_tf.GetID())
  backward_body_tf.SetAndObserveTransformNodeID(body_tf.GetID())
  backward_head_tf.SetAndObserveTransformNodeID(head_tf.GetID())
  backward_head_special_tf.SetAndObserveTransformNodeID(head_special_tf.GetID())
  getNode('body_inserts').SetAndObserveTransformNodeID(backward_body_tf.GetID())
  getNode('head_inserts').SetAndObserveTransformNodeID(backward_head_tf.GetID())
  getNode('head_special_insert').SetAndObserveTransformNodeID(backward_head_special_tf.GetID())

# clear current label map slice and draw ROIs based on the markups (radius in markup description)
def draw():
  # exclude boundaries from the head and body background ROIs:
  TOL_HEAD_PART            = 5  # mm from the head phantom boundary
  R_AND_TOL_AROUND_INSERTS = 20 # mm from the middle of the insert
  TOL_OUTER_EDGE           = 10 # mm from the body outer boundary
  
  labelNode = slicer.util.getNode('inserts-label')
  offset = slicer.app.layoutManager().sliceWidget("Red").mrmlSliceNode().GetSliceOffset()
  mat=vtk.vtkMatrix4x4()
  labelNode.GetRASToIJKMatrix(mat)
  K = round(mat.MultiplyPoint([0,0 ,offset,1])[2])
  label_vol = slicer.util.arrayFromVolume(labelNode)
  slice = label_vol[K,:,:]
  slice[:] = 0
  xv,yv = np.meshgrid(np.arange(slice.shape[0]),np.arange(slice.shape[1]))
  shape = xv.shape
  v0,v1 = np.array(xv).flatten(), np.array(yv).flatten()
  v2,v3 = v0*0+K, v0*0+1
  stack = np.vstack((v0,v1,v2,v3))
  mat_ijk=vtk.vtkMatrix4x4()
  labelNode.GetIJKToRASMatrix(mat_ijk)
  m=np.zeros((4,4))
  for i in range(4):
    for j in range(4):
      m[i,j] = mat_ijk.GetElement(i,j)
  out=np.matmul(m,stack)
  X = out[0,:].reshape(shape)
  Y = out[1,:].reshape(shape)
  R_list,ras_list = [],[]
  for markup_name in ('head_inserts','head_special_insert','body_inserts'):
    p = getNode(markup_name)
    for N in range(p.GetNumberOfControlPoints()):
      ras_list.append(p.GetNthControlPointPositionWorld(N))
      R_list.append(float(p.GetNthControlPointDescription(N)))
  label_inds = (1,3,4,5,6,7,8,9,10,2,11,12,13,14,15,16)
  for (r,a,s),ind,R_curr in zip(ras_list,label_inds,R_list):
    if ind == 1:
       #slice[(((r-X)/(200-TOL_OUTER_EDGE))**2+((a-Y)/(150-TOL_OUTER_EDGE))**2) <= 1] = 18
       slice[((r-X)**2+(a-Y)**2)**0.5 <= (100+TOL_HEAD_PART)] = 0
       slice[((r-X)**2+(a-Y)**2)**0.5 <= (100-TOL_HEAD_PART)] = 17
    slice[((r-X)**2+(a-Y)**2)**0.5 <= R_AND_TOL_AROUND_INSERTS] = 0
    slice[((r-X)**2+(a-Y)**2)**0.5 <= R_curr] = ind
  # only inlcude the largest continuous section of label 17 (head phantom uniform bg) and 18 (body unif bg)
  for ind in [17]: #[17,18]:
    l,n = ndimage.label(slice == ind)
    mask = (l == (np.argmax([np.sum(l == i) for i in range(1,n+1)])+1))
    slice[(mask == 0) & (slice == ind)] = 0
  
  # update label
  slicer.util.arrayFromVolumeModified(labelNode)

# interpolate between orphan label slices
def interpolate():
  labelNode = slicer.util.getNode('inserts-label')
  label_data = labelNode.GetImageData()
  interpolator = vtkITK.vtkITKMorphologicalContourInterpolator()
  interpolator.SetInputData(label_data)
  interpolator.Update()
  labelNode.SetAndObserveImageData(interpolator.GetOutput())

# replace label map with segmentation
def segm():
  for node in getNodes("inserts-segm").values():
    slicer.mrmlScene.RemoveNode(node)
  labelmapVolumeNode = getNode("inserts-label")
  seg = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode","inserts-segm")
  slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelmapVolumeNode, seg)
  seg.CreateClosedSurfaceRepresentation()
  slicer.mrmlScene.RemoveNode(labelmapVolumeNode)

# move red slice +/- in mm
def move(D):
  offset = slicer.app.layoutManager().sliceWidget("Red").mrmlSliceNode().GetSliceOffset()
  slicer.app.layoutManager().sliceWidget("Red").mrmlSliceNode().SetSliceOffset(offset+D)

def move_minus35():
    move(-35)

def move_plus70():
    move(70)

def verify_restart():
	if qt.QMessageBox.question(slicer.util.mainWindow(),"Warning","Restart?",qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
		slicer.util.restart()


def select_transforms():
    slicer.util.selectModule('Transforms')

def select_segmentstatistics():
    slicer.util.selectModule('SegmentStatistics')

def select_segmenteditor():
    slicer.util.selectModule('SegmentEditor')


slicer.util.mainWindow().addToolBarBreak()
tb = slicer.util.mainWindow().addToolBar("Custom")
tb.addWidget(qt.QPushButton("Add")).defaultWidget().connect('clicked()',slicer.util.openAddVolumeDialog)
tb.addWidget(qt.QPushButton("Restart")).defaultWidget().connect('clicked()',verify_restart)
tb.addWidget(qt.QPushButton("1) Loc. phantom")).defaultWidget().connect('clicked()',locate)
tb.addWidget(qt.QPushButton("2) Move -35mm")).defaultWidget().connect('clicked()',move_minus35)
tb.addWidget(qt.QPushButton("3) Detect inserts")).defaultWidget().connect('clicked()',detect)
tb.addWidget(qt.QPushButton("(Transforms)")).defaultWidget().connect('clicked()',select_transforms)
tb.addWidget(qt.QPushButton("4) Draw to label")).defaultWidget().connect('clicked()',draw)
tb.addWidget(qt.QPushButton("5) Move +70mm")).defaultWidget().connect('clicked()',move_plus70)
tb.addWidget(qt.QPushButton("6) Interpolate")).defaultWidget().connect('clicked()',interpolate)
tb.addWidget(qt.QPushButton("7) Label to segm")).defaultWidget().connect('clicked()',segm)
tb.addWidget(qt.QPushButton("(Segm. statistics)")).defaultWidget().connect('clicked()',select_segmentstatistics)

init()

##
# run the following
#init()
#locate()
#move(-35)
#detect() # adjust accordingly
#draw()
#move(70) # adjust accordingly
#draw()
#interpolate()
#segm()
##
