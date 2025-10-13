import base64

def parse_result(result):
    outputs = [
                {
                    'key': 'RH_OUT:context_model_3dm',
                    'k': '{0;0;0}'
                },
            ]
    
    try:
        # Find the parameter with the 3DM data
        result3dm = None
        for d in result['values']:
            if d['ParamName'] == outputs[0]['key']:
                key = outputs[0]['k']
                if key in d['InnerTree'] and len(d['InnerTree'][key]) > 0:
                    result3dm = d['InnerTree'][key][0]['data']
                    break
        
        if result3dm is None:
            raise ValueError(f"No parameter with name '{outputs[0]['key']}' found in response")
        
        # Try to decode as base64 if it's a string
        if isinstance(result3dm, str):
            byte_array = base64.b64decode(result3dm)
            print(f"DECODING")
        else:
            # If it's already bytes, use as is
            byte_array = result3dm
            print(f"NO DECODING")
        
        return byte_array
        
    except Exception as e:
        raise ValueError(f"Error parsing Rhino.Compute result: {str(e)}")