from qgis.utils import iface
import math, shutil, os, re, time, tempfile
from datetime import datetime
from qgis import processing
from qgis.PyQt import QtWidgets, QtGui, QtCore
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import (QgsProcessingAlgorithm, QgsRectangle, QgsVectorLayer, QgsVectorLayerExporter, QgsProject, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsPointXY,
    QgsProcessingFeatureSourceDefinition, QgsLayerTreeGroup,
    QgsProcessingContext, QgsProcessingUtils, QgsReferencedRectangle, QgsProcessingParameterString, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsFeatureRequest, QgsProcessing, Qgis)

#Unique naming variable for each script run
tempFolder = QgsProcessingUtils.tempFolder() + '/'
scriptRunTime = datetime.now().strftime("%Y%m%d%H%M%S")

#Get the layers in current project
currentProject = QgsProject.instance()
qgisProjectName = os.path.splitext(os.path.basename(QgsProject.instance().fileName()))[0]

"""
#############################################################################################
Freya initial set up
"""

#Image we'll use for the GUI
backgroundImage = r"C:/Freya/Resources/FreyaJPG.jpg"pleaseAdjust

#QGIS project for rendering 
basemapRenderingProjectPath = "C:/Freya/Resources/BasemapRenderingProject.qgz"pleaseAdjust

#Get windows's login as a string, and just keep the first name
username = re.match(r'[A-Z][a-z]*', os.getlogin()).group()

#Know how to speak to the user
if username in ['John', 'David', 'Michael', 'Joseph', 'Daniel', 'James', 'Benjamin', 'Matthew', 'Andrew', 'Samuel', 'Isaac', 'Jacob', 'Joshua', 'Ethan', 'Ryan', 'Nathan', 'Luke', 'Adam', 'Peter', 'Charles']:
    genderedEndearment = 'big guy'
elif username in ['Mary','Jennifer','Patricia','Linda','Morgan','Susan','Margaret','Elizabeth','Sarah','Michelle','Lisa','Julie','Rebecca','Amanda','Christine','Catherine','Nicole','Emily','Sharon','Donna']:
    genderedEndearment = 'sis'
else:
    genderedEndearment = 'buddy'

"""
#############################################################################################################################################################
GUI set up
"""

# Kick off the Qt app — this creates the GUI event loop
guiEventLoop = QtCore.QEventLoop()

#Create a window with a 800x800 pixel size
window = QtWidgets.QWidget()
window.setWindowTitle("Freya")
window.resize(800, 800)

#Window background as defined by the file path backgroundImage
backgroundLabel = QtWidgets.QLabel(window)
pixmap = QtGui.QPixmap(backgroundImage)
backgroundLabel.setPixmap(pixmap.scaled(window.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
backgroundLabel.setGeometry(0, 0, window.width(), window.height())

#Make sure that when you resize the window things actually shift around properly
window.resizeEvent = lambda event: (backgroundLabel.setGeometry(0, 0, window.width(), window.height()) or
    backgroundLabel.setPixmap(pixmap.scaled(window.size(), QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)))

#Set up the layout of the window
layout = QtWidgets.QVBoxLayout()
layout.setContentsMargins(10, 10, 10, 10)

#Add a stretch to make sure that the gap to the background image is at the top)
layout.addStretch()

#Message box where the user's and Freya's messages come through
messageBox = QtWidgets.QTextEdit()
messageBox.setReadOnly(True)
messageBox.setFont(QtGui.QFont("Ebrima", 11))
messageBox.viewport().setAutoFillBackground(True)
messageBox.setStyleSheet("QTextEdit { background: rgba(255, 255, 255, 200); }")
messageBox.setFixedHeight(250)
layout.addWidget(messageBox)

#Input box where the user types their messages
inputLine = QtWidgets.QLineEdit()
inputLine.setFont(QtGui.QFont("Ebrima", 11))
inputLine.setAutoFillBackground(True)
inputLine.setStyleSheet("QLineEdit { background: rgba(255, 255, 255, 200); }")
inputLine.setFixedHeight(30)
layout.addWidget(inputLine)

#Show the main window we just built and put it on the opposing screen
window.setLayout(layout)
screens = QtWidgets.QApplication.screens()
qgisCenter = iface.mainWindow().geometry().center()
otherScreen = next((s for s in screens if not s.geometry().contains(qgisCenter)), screens[0])
screenGeom = otherScreen.geometry()
window.move(screenGeom.center()/4)
window.show()
QtWidgets.QApplication.processEvents()

#Printing messages in the message feed
def messageFeed(text):
    messageBox.append(text)  #Chuck the text into the on-screen log box (QTextEdit)
    QtWidgets.QApplication.processEvents()  #Force the GUI to repaint right away

#Make a way to pause the script that doesn't block things
def pauseScript(seconds):
    endTime = QtCore.QTime.currentTime().addMSecs(int(seconds * 1000))
    while QtCore.QTime.currentTime() < endTime:
        QtWidgets.QApplication.processEvents()

"""
#############################################################################################################################################################
Beginning interaction with Freya
"""

messageFeed("")
pauseScript(0.2)
#Begin Freya's messages
messageFeed("Freya: Hey " + genderedEndearment + ", I'm Freya, I can make a QField project for you.")
pauseScript(1.4)  #Pause a sec like a real person — GUI will freeze during the sleeps
messageFeed("Freya: To get started I'll need you to pan the QGIS map frame to the area you want to export data from")
pauseScript(1.6)
messageFeed("Freya: You can drag the side panes inwards to make the viewport thinner, if this suits your project")
pauseScript(1)
messageFeed("Freya: Let me know when you're ready!")
inputLine.setFocus()  #Put cursor straight in so the user can start typing


currentStep = '1'
#Handling for when user hits enter
def handlePressingEnter():
    
    #If something breaks then a message will come to the chat
    try:
    
        #Bringing in the variable step from outside the fcuntion
        global currentStep
        
        #Get the user's text if enter is pressed
        inputText = inputLine.text().strip()
        if not inputText:
            messageFeed(username + ':')
            pauseScript(1)
            messageFeed("Freya: ...hi?")
            return  #If nothing has been typed then quit and wait for the next message

        """
        #############################################################################################################################################################
        Step 1 Making sure user has panned to area
        """

        if currentStep == '1':
            currentStep = 'N/A'
            
            #Remove the users text from the text box and show it in the feed (i.e message sent)
            inputLine.clear()
            messageFeed(username + ': ' + inputText)
            pauseScript(1)
            
            #Get the map frame extent
            global mapFrameExtent
            global mapFrameCrs
            mapFrameExtent = iface.mapCanvas().extent()
            mapFrameCrs = iface.mapCanvas().mapSettings().destinationCrs()
            
            messageFeed("Freya: Ok great")
            pauseScript(1.5)
            messageFeed("Freya: Now, tick on all the vector layers that you'd like to export to the QField project")
            pauseScript(1)
            messageFeed("Freya: As in, points, lines & polygons")
            pauseScript(1.2)
            messageFeed("Freya: Also tick on the basemap you want to use offline")
            pauseScript(1)
            messageFeed("Freya: Let me know when you're good to go")
            
            currentStep = '2'
            return 
        
        """
        #############################################################################################################################################################
        Step 2: Chooing the output folder via a pop up
        """

        if currentStep == '2':
            currentStep = 'N/A'
            
            #Get the layers that are currently visible
            layersInTree = currentProject.layerTreeRoot().findLayers()
            
            global visibleVectorLayers
            visibleVectorLayers = [lyr.layer() for lyr in layersInTree if lyr.isVisible() and isinstance(lyr.layer(), QgsVectorLayer)]
            global visibleRasterTileLayers
            visibleRasterTileLayers = [lyr.layer() for lyr in layersInTree if lyr.isVisible() and lyr.layer().providerType() in ('wms', 'xyz')]
            
            #Remove the users text from the text box and show it in the feed (i.e message sent)
            inputLine.clear()
            messageFeed(username + ': ' + inputText)
            pauseScript(1)
            messageFeed("Freya: Nice")
            pauseScript(1.2)
            messageFeed("Freya: So now we need to choose a folder to export the QField project to")
            pauseScript(1)
            
            
            global outputFolder
            outputFolder = ''
            
            outputFolder = QtWidgets.QFileDialog.getExistingDirectory(None,"Select Output Folder","",QtWidgets.QFileDialog.ShowDirsOnly)
            if outputFolder == '':
                messageFeed("Freya: Sorry darl, I didn't get your folder...")
                pauseScript(1)
                outputFolder = QtWidgets.QFileDialog.getExistingDirectory(None,"Select Output Folder","",QtWidgets.QFileDialog.ShowDirsOnly)
                if outputFolder == '':
                    #The user may want to quit the application after browsing for files
                    messageFeed("Freya: I think you're having some problems... Let me know when you're good to go again")
                    currentStep = '2'
                    return
            outputFolder = outputFolder.replace('\\','/').strip()
            
            pauseScript(0.6)
            messageFeed("Freya: Ok I got your output folder")
            pauseScript(1.2)
            messageFeed("Freya: Now what pixel size do you want your offline basemap to be? In metres")
            pauseScript(1.5)
            messageFeed("Freya: For example, if you wanted a basemap that is 10000 pixels wide then you'd want a pixel size of " + str(math.ceil((mapFrameExtent.width()/10000) * 10) / 10))
            
            currentStep = '3'
            return
            
        """
        #############################################################################################################################################################
        Step 3: evaluating the pixel size
        """
            
        if currentStep == '3':
            currentStep = 'N/A'
            
            #Remove the users text from the text box and show it in the feed (i.e message sent)
            inputLine.clear()
            messageFeed(username + ': ' + inputText)
            pauseScript(1)
            
            try:
                float(inputText)
            except BaseException as e:
                messageFeed("Freya: Sorry darl, I'm going to need a valid number")
                currentStep = '3'
                return
            
            global pixelSize
            pixelSize = float(inputText)
            
            if (mapFrameExtent.width()/pixelSize) > 200000:
                messageFeed("Freya: Nah this will take an absurb amount of time to export, best increase that pixel size a bit...")
                pauseScript(1.5)
                messageFeed("Freya: What would you like to increase the pixel size to?")
                currentStep = '3'
                return
            elif (mapFrameExtent.width()/pixelSize) > 50000:
                messageFeed("Freya: This will take a very long time to export with this pixel size, and it may be wise to leave it going overnight")
                pauseScript(1.5)
                messageFeed("Freya: Are you happy to start it up?")
                currentStep = '4'
                return
            elif (mapFrameExtent.width()/pixelSize) > 20000:
                messageFeed("Freya: This is a pretty hefty basemap export, it'll probably take a while")
                pauseScript(1.5)
                messageFeed("Freya: Are you happy to keep going with this pixel size?")
                currentStep = '4'
                return
            elif (mapFrameExtent.width()/pixelSize) < 2000:
                messageFeed("Freya: This is a tiny image")
                if genderedEndearment == 'big guy':
                    pauseScript(1)
                    messageFeed("Freya: I reckon you could handle a bigger image than this, big boy") 
                pauseScript(1)
                messageFeed("Freya: Are you happy to stick with this pixel size?")
                currentStep = '4'
                return

            messageFeed("Freya: Yeah awesome")
            pauseScript(1.5)
            messageFeed("Freya: So basically from here, all you need to do is click run in the window that is about to pop up")
            pauseScript(1.2)
            messageFeed("Freya: Once the process has finished you can transfer the zip folder to your phone")
            pauseScript(1)
            messageFeed("Freya: Reckon you can handle that? Good luck!")
            pauseScript(1.2)
            
            #Quit the dialog, so that we go to the processing window
            guiEventLoop.quit()
            
        """
        #############################################################################################################################################################
        Step 4: dealing with large imagery requests
        """
        
        if currentStep == '4':
            currentStep = 'N/A'
            
            #Remove the users text from the text box and show it in the feed (i.e message sent)
            inputLine.clear()
            messageFeed(username + ': ' + inputText)
            pauseScript(1)
            
            #Strip off whitespacing and look for a y or a n
            if inputText.strip()[0] in ['Y','y']:
                messageFeed("Freya: Alrighty then")
                pauseScript(1.5)
                messageFeed("Freya: So basically from here, all you need to do is click run in the window that is about to pop up")
                pauseScript(1.2)
                messageFeed("Freya: Once the process has finished you can transfer the zip folder to your phone")
                pauseScript(1)
                messageFeed("Freya: Hopefully it won't take too long, good luck!")
                pauseScript(1)
                
                #Quit the dialog and run the processing tool
                guiEventLoop.quit()

            elif inputText.strip()[0] in ['N','n']:
                currentStep = '3'
                messageFeed("Freya: Alright, tell me what pixel size you'd like to aim for instead")
            else:
                messageFeed("Freya: I need a yes or a no, honey")
                currentStep = '4'
                
    except BaseException as e:
        messageFeed(str(e))
        messageFeed("Freya: Uh oh, we got an error... That wasn't supposed to happen")
        
#When the user presses enter, something will happen
inputLine.returnPressed.connect(handlePressingEnter)

#Start up a loop where the interface remains open until the loop ends
guiEventLoop.exec_()
window.close()
QtWidgets.QApplication.processEvents()

"""
########################################################################################################################
########################################################################################################################
GUI loop finished, time for the processing script
"""


#Define a class so that it can use QgsProcessingAlgorithm stuff
class QFieldProjectSetup(QgsProcessingAlgorithm):

    #This part runs first to get the inputs given by the user, all this is for the user though is a little info window
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterString("info","Text box",defaultValue="All you need to do now is click 'Run' down in the bottom right.\n\nIf you have any issues please let the GIS team know.\n\nHope to see you again soon!\n\n  - Freya",
                multiLine=True,optional=True))
                
    """
    #############################################################################################
    Actual processing
    """

    #This is the part that runs and actually does the processing work
    def processAlgorithm(self, parameters, context, feedback):
        
        #See how it goes and raise an exception if need be
        try:
           
            outputSubFolder = outputFolder + '/' + qgisProjectName + scriptRunTime
            os.makedirs(outputSubFolder, exist_ok=True)
            
            #Make a copy of the QField base project into the output folder
            shutil.copy(currentProject.fileName(), outputSubFolder + '/' + qgisProjectName + '_QfieldProj.qgz')
            qFieldProject = QgsProject()
            qFieldProject.read(outputSubFolder + '/' + qgisProjectName + '_QfieldProj.qgz')
            
            """
            #############################################################################################
            Creation of the basemap imagery
            """
            
            #The pixel size specified by the user must be converted to a zoom level for the mbtiles
            zoomLevel = math.log2(156543 / pixelSize)
            zoomLevel = math.floor(zoomLevel)
            
            #The mbtiles seems to require a wgs extent 
            transform = QgsCoordinateTransform(mapFrameCrs, QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())
            lowerLeftCorner = transform.transform(QgsPointXY(mapFrameExtent.xMinimum(), mapFrameExtent.yMinimum()))
            upperRightCorner = transform.transform(QgsPointXY(mapFrameExtent.xMaximum(), mapFrameExtent.yMaximum()))
            extentWgs = QgsRectangle(lowerLeftCorner, upperRightCorner)
            
            #The clean basemap project is used for rendering mbtiles, given that whatever is shown in the map frame becomes rendered when using native:tilesxyzmbtiles
            basemapProject = QgsProject()
            basemapProject.read(basemapRenderingProjectPath)
            basemapProjectContext = QgsProcessingContext()
            basemapProjectContext.setProject(basemapProject)
            
            #Get the basemap from the project
            if visibleRasterTileLayers:
                firstRasterLayer = visibleRasterTileLayers[0]
                basemapProject.addMapLayer(firstRasterLayer.clone())          
            
            #Rendering the map frame as .mbtiles
            processing.run("native:tilesxyzmbtiles", {'EXTENT':extentWgs,'ZOOM_MIN':zoomLevel,'ZOOM_MAX':zoomLevel,'DPI':150,
                'ANTIALIAS':True,'TILE_FORMAT':1,'QUALITY':95,'METATILESIZE':16,
                'OUTPUT_FILE':tempFolder + 'BasemapMB' + scriptRunTime + '.mbtiles'},context=basemapProjectContext, feedback=feedback)
            
            #Warp it to a .tif, and set the compression to WEBP
            processing.run("gdal:warpreproject", {'INPUT':tempFolder + 'BasemapMB' + scriptRunTime + '.mbtiles','SOURCE_CRS':None,'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:28355'),
                'RESAMPLING':2,'NODATA':None,'TARGET_RESOLUTION':pixelSize,'OPTIONS':'COMPRESS=WEBP|NUM_THREADS=ALL_CPUS|TILED=YES|BIGTIFF=IF_SAFER|WEBP_LEVEL=90',
                'DATA_TYPE':0,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'EXTRA':'','OUTPUT':outputSubFolder + '/Basemap' + scriptRunTime + '.tif'},feedback=feedback)

            #WEBP compressed pyramids
            processing.run("gdal:overviews", {'INPUT':outputSubFolder + '/Basemap' + scriptRunTime + '.tif','CLEAN':False,'LEVELS':'','RESAMPLING':3,'FORMAT':1,
                'EXTRA':'--config COMPRESS_OVERVIEW WEBP'},feedback=feedback)
            
            #Load the basemap layer into the project at the bottom
            basemapLayer = QgsRasterLayer(outputSubFolder + '/Basemap' + scriptRunTime + '.tif', 'OfflineBasemap')
            qFieldProject.addMapLayer(basemapLayer)
            projectRootTree = qFieldProject.layerTreeRoot()
            basemapLayerNode = projectRootTree.findLayer(basemapLayer.id())
            projectRootTree.insertChildNode(len(projectRootTree.children()), basemapLayerNode.clone())
            projectRootTree.removeChildNode(basemapLayerNode)

            #Save the project
            qFieldProject.write()
            
            """
            #############################################################################################
            Clipping of all of the vector layers to the chosen extent
            and pointing the layers to the new versions of the files
            """
            
            #Go through all of the vector layers in the copied project
            allVectorLayers = [layer for layer in qFieldProject.mapLayers().values() if isinstance(layer, QgsVectorLayer)]
            layersToRemove = []
            for vectorLayer in allVectorLayers:
                try:
              
                    #Get rid of any layer that isn't ticked on, otherwise grab the source of the original
                    correspondingVisibleLayer = next((layer for layer in visibleVectorLayers if layer.id() == vectorLayer.id()), None)
                    if not correspondingVisibleLayer:
                        layersToRemove.append(vectorLayer.id())
                        continue
                    
                    else:
                        #Having forward slashes in layer names makes the output glitch
                        cleanedName = correspondingVisibleLayer.name().replace('/','-')
                        
                        #Handling for conversion of a shapefile to a gpkg when the shp has an fid column
                        if correspondingVisibleLayer.source().lower().endswith(".shp") and 'fid' in [field.name() for field in correspondingVisibleLayer.fields()]:
                            #Find a spot to save the shapefile with fid removed
                            tempFilePath = tempfile.NamedTemporaryFile(suffix='.gpkg', delete=False).name
                            #Save out the temp layer with no fid
                            processing.run("native:deletecolumn", {'INPUT':correspondingVisibleLayer,'COLUMN':['fid'],'OUTPUT':tempFilePath}, feedback = feedback)['OUTPUT']
                            #Get the source so that invalid geometries can be ignored
                            correspondingVisibleLayerSource = QgsProcessingFeatureSourceDefinition(tempFilePath,selectedFeaturesOnly=False,featureLimit=-1,flags=Qgis.ProcessingFeatureSourceDefinitionFlag.OverrideDefaultGeometryCheck,geometryCheck=Qgis.InvalidGeometryCheck.NoCheck)
                            
                        #Otherwise we can just point straight at the source
                        else:
                            correspondingVisibleLayerSource = QgsProcessingFeatureSourceDefinition(correspondingVisibleLayer.id(), selectedFeaturesOnly=False, featureLimit=-1, flags=Qgis.ProcessingFeatureSourceDefinitionFlag.OverrideDefaultGeometryCheck, geometryCheck=Qgis.InvalidGeometryCheck.NoCheck)
                        
                        #If it's a spatial layer then only get the features in the layer that appear in the extent (note that clipping is not enabled)
                        if correspondingVisibleLayer.isSpatial():
                            processing.run("native:extractbyextent", {'INPUT':correspondingVisibleLayerSource,'EXTENT':mapFrameExtent,'CLIP':False,'OUTPUT':outputSubFolder + '/' + cleanedName + scriptRunTime + '.gpkg'})
                        
                        #Otherwise, if it's just a table, then just save it out
                        else:
                            processing.run("native:fieldcalculator", {'INPUT': correspondingVisibleLayerSource, 'FIELD_NAME': 'QFieldExportDate', 'FIELD_TYPE': 2, 'FIELD_LENGTH': 10, 'FIELD_PRECISION': 0, 'FORMULA': "'" + datetime.now().date().isoformat() + "'",
                                'OUTPUT': outputSubFolder + '/' + cleanedName + scriptRunTime + '.gpkg'}, feedback=feedback)

                        #Re-point the layer to the new clipped version
                        vectorLayer.setDataSource(outputSubFolder + '/' + cleanedName + scriptRunTime + '.gpkg', vectorLayer.name(), "ogr")
                        feedback.pushInfo('Loaded up ' + cleanedName + scriptRunTime + '.gpkg')
                    
                except BaseException as e:
                    feedback.reportError(str(e))
                    
            #Remove the layers that aren't ticked on
            for layerId in layersToRemove:
                qFieldProject.removeMapLayer(layerId)
            qFieldProject.write()

            #Remove the empty groups from the project 
            def removeEmptyGroups(group):
                for child in list(group.children()):
                    if isinstance(child, QgsLayerTreeGroup):
                        removeEmptyGroups(child)
                        if len(child.children()) == 0:
                            group.removeChildNode(child)
            removeEmptyGroups(qFieldProject.layerTreeRoot())

            """
            #############################################################################################
            Finishing up
            """
            
            #Now put the whole lot in a zip folder
            shutil.make_archive(base_name=outputSubFolder, format='zip', root_dir=outputSubFolder, base_dir='.')
        
        except BaseException as e:
            feedback.reportError(str(e))
        
        #Return nothing because you have to return something
        return {}
        
    """
    ###############################################################
    Final definitions of processing script parameters
    """

    def name(self):
        return 'freya'

    def displayName(self):
        return 'Freya'

    def group(self):
        return 'Custom Scripts'

    def groupId(self):
        return 'customscripts'

    def createInstance(self):
        return QFieldProjectSetup()
