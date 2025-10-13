import compute_rhino3d.Util
import compute_rhino3d.Grasshopper as gh
import rhino3dm
import json
from compute_rhino3dm_helpers import add_parameter, decode_gh_output, save_3dm_file

compute_rhino3d.Util.url = "http://localhost:6500/"
#compute_rhino3d.Util.apiKey = ""

pt1 = rhino3dm.Point3d(0, 0, 0)
circle = rhino3dm.Circle(pt1, 5)
angle = 20
print(f'origina curcle: {circle}')

# convert circle to curve and stringify
curve = json.dumps(circle.ToNurbsCurve().Encode())
print(curve)

curve = add_parameter("RH_IN:curve", curve)
rotate = add_parameter("RH_IN:rotate", angle)

print(curve)

gh_inputs = [curve, rotate]

print(gh_inputs)
output = gh.EvaluateDefinition('../assets/twisty.gh', gh_inputs)
# print(output)

# decode results

# print(output)
# branch = output['values'][0]['InnerTree']['{0;0}']


# lines = [rhino3dm.CommonObject.Decode(json.loads(item['data'])) for item in branch]
# print(lines)

lines = decode_gh_output(output)

print(f'lines: {lines}')
filename = '../assets/twisty.3dm'

print('Writing {} lines to {}'.format(len(lines), filename))

# # create a 3dm file with results
# model = rhino3dm.File3dm()
# for l in lines:
#     model.Objects.AddCurve(l) # they're actually LineCurves...

# model.Write(filename)

save_3dm_file(lines, filename)