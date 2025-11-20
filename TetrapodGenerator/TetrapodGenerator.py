# TetrapodGenerator.py
# Fusion 360 Add-in - 最終完成版

import adsk.core, adsk.fusion, traceback
import math

_app = None
_ui = None
_handlers = []

# 初期設定
LEG_LENGTH = 8.0  # cm
LEG_BASE_DIAMETER = 5.0  # cm
LEG_TIP_DIAMETER = 4.0  # cm
CENTER_FILLET_RADIUS = 2.5  # cm（接合部のみ）
TIP_FILLET_RADIUS = 0.3  # cm（先端の角丸）

def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        
        cmdDef = _ui.commandDefinitions.itemById('TetrapodGenerator')
        if cmdDef:
            cmdDef.deleteMe()
        
        cmdDef = _ui.commandDefinitions.addButtonDefinition(
            'TetrapodGenerator',
            'テトラポッド生成 🏗️',
            'リアルなテトラポッドを生成'
        )
        
        onCommandCreated = TetrapodCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)
        
        added = False
        try:
            utilPanel = _ui.allToolbarPanels.itemById('ToolsTab')
            if utilPanel:
                cntrl = utilPanel.controls.addCommand(cmdDef)
                cntrl.isPromotedByDefault = True
                cntrl.isPromoted = True
                added = True
        except:
            pass
        
        if not added:
            try:
                createPanel = _ui.allToolbarPanels.itemById('SolidCreatePanel')
                if createPanel:
                    cntrl = createPanel.controls.addCommand(cmdDef)
                    cntrl.isPromotedByDefault = True
                    added = True
            except:
                pass
        
        if added:
            _ui.messageBox('✅ アドオン読み込み完了!')
        
    except:
        if _ui:
            _ui.messageBox('❌ 失敗:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        for panelId in ['ToolsTab', 'SolidCreatePanel']:
            try:
                panel = _ui.allToolbarPanels.itemById(panelId)
                if panel:
                    cmd = panel.controls.itemById('TetrapodGenerator')
                    if cmd:
                        cmd.deleteMe()
            except:
                pass
        
        cmdDef = _ui.commandDefinitions.itemById('TetrapodGenerator')
        if cmdDef:
            cmdDef.deleteMe()
    except:
        pass

class TetrapodCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            
            inputs.addValueInput('legLength', '脚の長さ (cm)', 'cm', 
                                adsk.core.ValueInput.createByReal(LEG_LENGTH))
            inputs.addValueInput('legBaseDiameter', '脚の根元直径 (cm)', 'cm',
                                adsk.core.ValueInput.createByReal(LEG_BASE_DIAMETER))
            inputs.addValueInput('legTipDiameter', '脚の先端直径 (cm)', 'cm',
                                adsk.core.ValueInput.createByReal(LEG_TIP_DIAMETER))
            inputs.addValueInput('centerFilletRadius', '接合部フィレット半径 (cm)', 'cm',
                                adsk.core.ValueInput.createByReal(CENTER_FILLET_RADIUS))
            inputs.addValueInput('tipFilletRadius', '先端角丸半径 (cm)', 'cm',
                                adsk.core.ValueInput.createByReal(TIP_FILLET_RADIUS))
            
            onExecute = TetrapodCommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)
            
        except:
            _ui.messageBox('UI作成失敗:\n{}'.format(traceback.format_exc()))

class TetrapodCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        try:
            inputs = args.command.commandInputs
            
            legLength = inputs.itemById('legLength').value
            legBaseDiameter = inputs.itemById('legBaseDiameter').value
            legTipDiameter = inputs.itemById('legTipDiameter').value
            centerFilletRadius = inputs.itemById('centerFilletRadius').value
            tipFilletRadius = inputs.itemById('tipFilletRadius').value
            
            createTetrapod(legLength, legBaseDiameter, legTipDiameter, 
                          centerFilletRadius, tipFilletRadius)
            
            _ui.messageBox('🎉 テトラポッド生成完了!')
            
        except:
            _ui.messageBox('生成失敗:\n{}'.format(traceback.format_exc()))

def createTetrapod(legLength, legBaseDiameter, legTipDiameter, 
                   centerFilletRadius, tipFilletRadius):
    """テトラポッド生成"""
    
    design = _app.activeProduct
    rootComp = design.rootComponent
    
    occurrence = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occurrence.component
    comp.name = 'Tetrapod'
    
    # 正四面体配置
    legVectors = [
        (0, 0, 1),
        (2*math.sqrt(2)/3, 0, -1/3),
        (-math.sqrt(2)/3, math.sqrt(2/3), -1/3),
        (-math.sqrt(2)/3, -math.sqrt(2/3), -1/3)
    ]
    
    for vec in legVectors:
        createLeg(comp, legLength, legBaseDiameter, legTipDiameter, vec)
    
    # 結合
    combineAllBodies(comp)
    
    # 先端の角丸（先に実行）
    addTipFillets(comp, tipFilletRadius)
    
    # 接合部のフィレット（後で実行）
    addCenterFillets(comp, centerFilletRadius)

def createLeg(comp, length, baseDiameter, tipDiameter, direction):
    """脚作成"""
    
    sketches = comp.sketches
    xyPlane = comp.xYConstructionPlane
    
    # 根元
    baseSketch = sketches.add(xyPlane)
    baseRadius = baseDiameter / 2
    baseSketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0),
        baseRadius
    )
    
    # 先端平面
    planes = comp.constructionPlanes
    planeInput = planes.createInput()
    offsetValue = adsk.core.ValueInput.createByReal(length)
    planeInput.setByOffset(xyPlane, offsetValue)
    tipPlane = planes.add(planeInput)
    
    # 先端
    tipSketch = sketches.add(tipPlane)
    tipRadius = tipDiameter / 2
    tipSketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0),
        tipRadius
    )
    
    # Loft
    lofts = comp.features.loftFeatures
    loftInput = lofts.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    
    loftSections = loftInput.loftSections
    loftSections.add(baseSketch.profiles.item(0))
    loftSections.add(tipSketch.profiles.item(0))
    
    loftInput.isSolid = True
    loftFeature = lofts.add(loftInput)
    
    body = loftFeature.bodies.item(0)
    rotateBody(comp, body, direction)
    
    tipPlane.deleteMe()

def rotateBody(comp, body, direction):
    """回転"""
    
    x, y, z = direction
    
    defaultDir = adsk.core.Vector3D.create(0, 0, 1)
    targetDir = adsk.core.Vector3D.create(x, y, z)
    targetDir.normalize()
    
    angle = defaultDir.angleTo(targetDir)
    
    if angle > 0.001:
        axis = defaultDir.crossProduct(targetDir)
        axis.normalize()
        
        origin = adsk.core.Point3D.create(0, 0, 0)
        transform = adsk.core.Matrix3D.create()
        transform.setToRotation(angle, axis, origin)
        
        moveFeats = comp.features.moveFeatures
        bodyCol = adsk.core.ObjectCollection.create()
        bodyCol.add(body)
        
        moveInput = moveFeats.createInput(bodyCol, transform)
        moveFeats.add(moveInput)

def combineAllBodies(comp):
    """結合"""
    
    bodies = comp.bRepBodies
    if bodies.count < 2:
        return
    
    targetBody = bodies.item(0)
    toolBodies = adsk.core.ObjectCollection.create()
    
    for i in range(1, bodies.count):
        toolBodies.add(bodies.item(i))
    
    combines = comp.features.combineFeatures
    combineInput = combines.createInput(targetBody, toolBodies)
    combineInput.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
    combineInput.isKeepToolBodies = False
    combines.add(combineInput)

def addTipFillets(comp, radius):
    """先端の円のエッジを角丸に"""
    
    bodies = comp.bRepBodies
    if bodies.count == 0:
        return
    
    body = bodies.item(0)
    fillets = comp.features.filletFeatures
    edgeCol = adsk.core.ObjectCollection.create()
    
    # 先端の円形エッジ（長いエッジ）を検出
    for edge in body.edges:
        # 円形のエッジは長さが一定範囲
        if 8 < edge.length < 15:  # 先端円周のエッジ
            edgeCol.add(edge)
    
    if edgeCol.count > 0:
        try:
            filletInput = fillets.createInput()
            filletInput.addConstantRadiusEdgeSet(
                edgeCol, 
                adsk.core.ValueInput.createByReal(radius), 
                True
            )
            fillets.add(filletInput)
        except:
            pass

def addCenterFillets(comp, radius):
    """接合部のフィレット（中心部のみ）"""
    
    bodies = comp.bRepBodies
    if bodies.count == 0:
        return
    
    body = bodies.item(0)
    fillets = comp.features.filletFeatures
    edgeCol = adsk.core.ObjectCollection.create()
    
    # 中心付近の短いエッジのみ選択
    centerPoint = adsk.core.Point3D.create(0, 0, 0)
    
    for edge in body.edges:
        # エッジの中点を取得
        evaluator = edge.evaluator
        success, startParam, endParam = evaluator.getParameterExtents()
        if success:
            midParam = (startParam + endParam) / 2
            success, midPoint = evaluator.getPointAtParameter(midParam)
            
            if success:
                # 中心から近い & 短いエッジ
                distance = centerPoint.distanceTo(midPoint)
                if distance < radius * 2 and edge.length < radius * 1.5:
                    edgeCol.add(edge)
    
    if edgeCol.count > 0:
        try:
            filletInput = fillets.createInput()
            filletInput.addConstantRadiusEdgeSet(
                edgeCol, 
                adsk.core.ValueInput.createByReal(radius), 
                True
            )
            filletInput.isG2 = False
            filletInput.isRollingBallCorner = True
            fillets.add(filletInput)
        except:
            pass