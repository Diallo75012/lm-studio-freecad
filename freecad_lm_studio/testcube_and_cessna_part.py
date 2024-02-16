import FreeCAD as App
import Part
import math
import vtk
from vtk.util.numpy_support import vtk_to_numpy


# STL to PNG conversion function remains unchanged
def stl_to_png(stl_path, png_path):
    # Create a reader for the STL file
    reader = vtk.vtkSTLReader()
    reader.SetFileName(stl_path)

    # Create a mapper for the STL data
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    # Create an actor to represent the STL model
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # Set up a renderer
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(0.1, 0.2, 0.4)  # Change background color to see the object more clearly

    # Set up the camera to focus on the object
    renderer.ResetCamera()
    camera = renderer.GetActiveCamera()
    camera.Azimuth(30)
    camera.Elevation(30)

    # Improve lighting
    renderer.LightFollowCameraOn()
    renderer.TwoSidedLightingOn()

    # Create a render window
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindow.SetOffScreenRendering(1)  # Enable off-screen rendering
    renderWindow.SetSize(800, 600)

    # Render the scene
    renderWindow.Render()

    # Capture the rendered image to a vtkWindowToImageFilter
    windowToImageFilter = vtk.vtkWindowToImageFilter()
    windowToImageFilter.SetInput(renderWindow)
    windowToImageFilter.Update()

    # Write the image to a file
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(png_path)
    writer.SetInputConnection(windowToImageFilter.GetOutputPort())
    writer.Write()


def stl_to_png(stl_path, png_path):
    # Create a reader for the STL file
    reader = vtk.vtkSTLReader()
    reader.SetFileName(stl_path)

    # Create a mapper for the STL data
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    # Create an actor to represent the STL model
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # Set up a renderer
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(0.1, 0.2, 0.4)  # Change background color to see the object more clearly

    # Set up the camera to focus on the object with a dynamic angle
    renderer.ResetCamera()
    camera = renderer.GetActiveCamera()
    camera.SetPosition(0, -1, 1)  # Adjust this to change the camera's position
    camera.SetFocalPoint(0, 0, 0)  # Adjust this to change where the camera is looking
    camera.SetViewUp(0, 0, 1)  # Adjust this to change the "up" direction of the camera
    camera.Azimuth(30)  # Rotates the camera about the view up vector
    camera.Elevation(20)  # Rotates the camera about the cross product of the direction of projection and the view up vector

    # Improve lighting
    renderer.LightFollowCameraOn()
    renderer.TwoSidedLightingOn()

    # Create a render window
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindow.SetOffScreenRendering(1)  # Enable off-screen rendering
    renderWindow.SetSize(800, 600)

    # Render the scene
    renderWindow.Render()

    # Capture the rendered image to a vtkWindowToImageFilter
    windowToImageFilter = vtk.vtkWindowToImageFilter()
    windowToImageFilter.SetInput(renderWindow)
    windowToImageFilter.Update()

    # Write the image to a file
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(png_path)
    writer.SetInputConnection(windowToImageFilter.GetOutputPort())
    writer.Write()


# Function to create a simple box and export it as STL, then convert to PNG
def create_box_export_stl_and_convert_to_png():
    length = 10
    width = 10
    height = 10

    # Create a box shape directly without adding it to a document
    box = Part.makeBox(length, width, height)

    # Export the shape to an STL file
    stl_path = 'testcube.stl'
    box.exportStl(stl_path)

    # Convert the STL file to PNG
    png_path = 'testcube.png'
    stl_to_png(stl_path, png_path)

# Function to create a more complex model like a Cessna and export it as STL, then convert to PNG
def create_cessna_export_stl_and_convert_to_png():
    # Create parts of the Cessna
    fuselage = Part.makeCylinder(2, 20)
    wing = Part.makeBox(40, 4, 0.2, App.Vector(-20, -2, 2))
    tail = Part.makeBox(6, 0.5, 2, App.Vector(-3, -0.25, 4))
    tail_wing = Part.makeBox(10, 2, 0.2, App.Vector(-5, -1, 4))

    # Combine parts to create a single shape
    cessna = fuselage.fuse(wing).fuse(tail).fuse(tail_wing)

    # Export the shape to an STL file
    stl_path = '/home/creditizens//freecad_lm-studio/freecadus/cessna.stl'
    cessna.exportStl(stl_path)

    # Convert the STL file to PNG
    png_path = '/home/creditizens//freecad_lm-studio/freecadus/cessna.png'
    stl_to_png(stl_path, png_path)

create_box_export_stl_and_convert_to_png()
create_cessna_export_stl_and_convert_to_png()


"""

import FreeCAD as App
import Part
import math
import vtk
from vtk.util.numpy_support import vtk_to_numpy


# STL to PNG conversion function remains unchanged
def stl_to_png(stl_path, png_path):
    # Create a reader for the STL file
    reader = vtk.vtkSTLReader()
    reader.SetFileName(stl_path)

    # Create a mapper for the STL data
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    # Create an actor to represent the STL model
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # Set up a renderer
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(0.1, 0.2, 0.4)  # Change background color to see the object more clearly

    # Set up the camera to focus on the object
    renderer.ResetCamera()
    camera = renderer.GetActiveCamera()
    camera.Azimuth(30)
    camera.Elevation(30)

    # Improve lighting
    renderer.LightFollowCameraOn()
    renderer.TwoSidedLightingOn()

    # Create a render window
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindow.SetOffScreenRendering(1)  # Enable off-screen rendering
    renderWindow.SetSize(800, 600)

    # Render the scene
    renderWindow.Render()

    # Capture the rendered image to a vtkWindowToImageFilter
    windowToImageFilter = vtk.vtkWindowToImageFilter()
    windowToImageFilter.SetInput(renderWindow)
    windowToImageFilter.Update()

    # Write the image to a file
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(png_path)
    writer.SetInputConnection(windowToImageFilter.GetOutputPort())
    writer.Write()


def stl_to_png(stl_path, png_path):
    # Create a reader for the STL file
    reader = vtk.vtkSTLReader()
    reader.SetFileName(stl_path)

    # Create a mapper for the STL data
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    # Create an actor to represent the STL model
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # Set up a renderer
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(0.1, 0.2, 0.4)  # Change background color to see the object more clearly

    # Set up the camera to focus on the object with a dynamic angle
    renderer.ResetCamera()
    camera = renderer.GetActiveCamera()
    camera.SetPosition(0, -1, 1)  # Adjust this to change the camera's position
    camera.SetFocalPoint(0, 0, 0)  # Adjust this to change where the camera is looking
    camera.SetViewUp(0, 0, 1)  # Adjust this to change the "up" direction of the camera
    camera.Azimuth(30)  # Rotates the camera about the view up vector
    camera.Elevation(20)  # Rotates the camera about the cross product of the direction of projection and the view up vector

    # Improve lighting
    renderer.LightFollowCameraOn()
    renderer.TwoSidedLightingOn()

    # Create a render window
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindow.SetOffScreenRendering(1)  # Enable off-screen rendering
    renderWindow.SetSize(800, 600)

    # Render the scene
    renderWindow.Render()

    # Capture the rendered image to a vtkWindowToImageFilter
    windowToImageFilter = vtk.vtkWindowToImageFilter()
    windowToImageFilter.SetInput(renderWindow)
    windowToImageFilter.Update()

    # Write the image to a file
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(png_path)
    writer.SetInputConnection(windowToImageFilter.GetOutputPort())
    writer.Write()


# Function to create a simple box and export it as STL, then convert to PNG
def create_box_export_stl_and_convert_to_png():
    length = 10
    width = 10
    height = 10

    # Create a box shape directly without adding it to a document
    box = Part.makeBox(length, width, height)

    # Export the shape to an STL file
    stl_path = 'testcube.stl'
    box.exportStl(stl_path)

    # Convert the STL file to PNG
    png_path = 'testcube.png'
    stl_to_png(stl_path, png_path)

# Function to create a more complex model like a Cessna and export it as STL, then convert to PNG
def create_cessna_export_stl_and_convert_to_png():
    # Create parts of the Cessna
    fuselage = Part.makeCylinder(2, 20)
    wing = Part.makeBox(40, 4, 0.2, App.Vector(-20, -2, 2))
    tail = Part.makeBox(6, 0.5, 2, App.Vector(-3, -0.25, 4))
    tail_wing = Part.makeBox(10, 2, 0.2, App.Vector(-5, -1, 4))

    # Combine parts to create a single shape
    cessna = fuselage.fuse(wing).fuse(tail).fuse(tail_wing)

    # Export the shape to an STL file
    stl_path = 'cessna.stl'
    cessna.exportStl(stl_path)

    # Convert the STL file to PNG
    png_path = 'cessna.png'
    stl_to_png(stl_path, png_path)

create_box_export_stl_and_convert_to_png()
create_cessna_export_stl_and_convert_to_png()

"""

"""
### FOR FLASK TO RUN SCRIPT
import subprocess
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/draw', methods=['GET'])
def draw():
    # Path to your FreeCAD script
    script_path = '/path/to/your/script.py'

    # Execute the script using FreeCAD's command-line interface
    command = f'/home/creditizens/freecad_lm-studio/freecadus/AppRun {script_path}'
    subprocess.run(command, shell=True, check=True)

    return jsonify({"status": "success", "message": "FreeCAD operation triggered"})

if __name__ == "__main__":
    app.run(debug=True)

"""
