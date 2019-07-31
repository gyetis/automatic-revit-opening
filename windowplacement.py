__author__ = "Gizem Yetis"
__mail__ = "gizemyetis93@gmail.com"

import clr

clr.AddReference("RevitNodes")
import Revit
clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

from System.Collections.Generic import *

class WindowPlacement:
	def __init__(self, doc, wall, furniture, window):
		self.doc = doc
		self.wall = wall
		self.furniture = furniture
		self.window = window
	
	# Define exterior and interior walls
	def elType(self):
		extWall = []
		intWall = []
		for e in self.wall:
			if e.WallType.Function == WallFunction.Exterior:
				extWall.append(e)
			elif e.WallType.Function == WallFunction.Interior:
				intWall.append(e)
			else:
				intWall == self.intWall
				extWall == self.extWall
		return extWall, intWall
	
	# Get wall curves and furniture location point to find closest wall to furniture
	def elLoc(self, walls):
		wallCrvs = []
		furniturePt = []
		for w in walls:
			wallCrvs.append(w.Location.Curve)
		for f in self.furniture:		
			furniturePt = f.Location.Point
		return wallCrvs, furniturePt
	
	# Find closest wall index to extract closest wall and closest wall curve
	def closest(self, wallCrvs, furniturePt):
		distances = [curve.Distance(furniturePt) for curve in wallCrvs]
		closestInd = distances.index(min(distances))
		return closestInd
	
	# Define window specs with reference to closest wall and middle point of the furniture	
	def openSpec(self, closestWallCrv, furniturePt):
		furnitureBBoxMax = self.furniture[0].BoundingBox[self.doc.ActiveView].Max
		furnitureBBoxMin = self.furniture[0].BoundingBox[self.doc.ActiveView].Min		
		sillHeight = furnitureBBoxMax[2]
		furnitureMidLoc = furniturePt - ((furnitureBBoxMax - furnitureBBoxMin) / 2)
		furnitureMidLoc = closestWallCrv.Project(furnitureMidLoc).XYZPoint
		return sillHeight, furnitureMidLoc
	
	# Place window on the closest wall right on the middle and highest location point of the furniture. 
	def createOpening(self, closestWall, windowLoc, sillHeight):
		if self.window.IsActive == False:
			self.window.Activate()
			self.doc.Regenerate()
		opening = self.doc.Create.NewFamilyInstance(windowLoc, self.window, closestWall,  Structure.StructuralType.NonStructural)
		opening.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM).Set(sillHeight)
		return opening
		
# Work with boolean toogle
def main():
	# Start transaction with the current Revit document
	doc = DocumentManager.Instance.CurrentDBDocument
	TransactionManager.Instance.EnsureInTransaction(doc)
		
	# Define Revit element categories
	wallCategory = BuiltInCategory.OST_Walls
	furnitureCategory = BuiltInCategory.OST_Furniture
	windowCategory = BuiltInCategory.OST_Windows
		
	# Extract Revit elements and window type to placed
	walls = FilteredElementCollector(doc).OfCategory(wallCategory).WhereElementIsNotElementType().ToElements()
	furniture = FilteredElementCollector(doc).OfCategory(furnitureCategory).WhereElementIsNotElementType().ToElements()
	window = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(windowCategory).ToElements()[0]
		
	# Extract walls and specs
	placement = WindowPlacement(doc, walls, furniture, window)
	extWalls, intWalls = placement.elType()
	extWallCurves, furniturePt = placement.elLoc(extWalls)
	
	# Extract closest wall and specs with reference to the furniture
	closestWallIndex = placement.closest(extWallCurves, furniturePt)
	closestWallCurve = extWallCurves[closestWallIndex]
	closestWall = extWalls[closestWallIndex]
	
	# Define window specs to be placed on the closest wall with reference to the furniture's middle point
	sillHeight, furnitureLoc = placement.openSpec(closestWallCurve, furniturePt)

	# Create opening on the wall
	placement.createOpening(closestWall, furnitureLoc, sillHeight)

	# End transaction	
	TransactionManager.Instance.TransactionTaskDone()

main()
