def homogenize_annotations(rec):
    annotations = rec.get('annotations')
    if not isinstance(annotations, dict):
        return

    rec['annotations'] = {
        k: (
            v['annotation_value']
            if isinstance(v, dict) and 'annotation_value' in v
            else v
        )
        for k, v in annotations.items()
    }
