from django.conf import settings
from formpack import FormPack

from .constants import (CHARTABLE_TYPES,
                        SPECIFIC_CHARTS_KEY, DEFAULT_CHARTS_KEY
                        )


def get_instances_for_userform_id(userform_id, submission=None):
    query = {'_userform_id': userform_id, '_deleted_at': {'$exists': False}}
    if submission:
        query['_id'] = submission
    return settings.MONGO_DB.instances.find(query)


def _kuids(asset, cache=False):
    '''
    TODO: Stub.

    :param Asset asset:
    :param bool cache:
    '''

    if not cache or not hasattr(asset, '_available_chart_uids'):
        survey = asset.content.get('survey', [])
        asset._available_chart_uids = list()
        for row in survey:
            if 'type' in row:
                row_type = row['type']
                if isinstance(row_type, dict):
                    row_type = row_type.keys()[0]
                if row_type in CHARTABLE_TYPES:
                    asset._available_chart_uids.append(row.get('$kuid'))

    return asset._available_chart_uids


def get_kuid_to_variable_name_map(asset):
    '''
    Retrieve a mapping from "kuids", which :py:mod:`formpack` is not aware of, 
    to the corresponding XLSForm variable name.

    :param Asset asset: The asset to make mappings for.
    :rtype: dict[basesting, basestring]
    '''

    survey_dict = asset.content.get('survey', [])
    kuid_to_variable_name_map = {row.get('$kuid'): row.get('name') for row in survey_dict}
    return kuid_to_variable_name_map


def data(asset, kuids, lang=None, fields=None, split_by=None):
    '''
    :param Asset asset:
    :param iterable kuids:
    :param basestring lang:
    :param fields:
    :type fields:
    :param split_by:
    :type split_by:
    '''
    schema = {
        "id_string": asset.deployment.xform_id_string,
        "version": 'v1',
        "content": asset.valid_xlsform_content(),
    }

    pack = FormPack([schema])
    report = pack.autoreport()
    fields = fields or [field.name for field in pack.get_fields_for_versions()]
    translations = pack.available_translations
    lang = lang or next(iter(translations), None)

    data = [("v1", get_instances_for_userform_id(asset.deployment.mongo_userform_id))]
    stats = report.get_stats(data, fields, lang, split_by).stats
    stats_by_variable_name = {s[0].name: (s[0].name,)+s[1:] for s in stats}

    available_kuids = set(_kuids(asset, cache=True))
    if kuids:
        available_kuids &= set(kuids)
    kuid_to_variable_name_map = get_kuid_to_variable_name_map(asset)
    stats_by_kuid = {kuid: stats_by_variable_name[kuid_to_variable_name_map[kuid]]
                     for kuid in available_kuids}
    if not asset.chart_styles:
        asset._populate_chart_styles()
    default_style = asset.chart_styles[DEFAULT_CHARTS_KEY]
    specified = asset.chart_styles[SPECIFIC_CHARTS_KEY]
    chart_styles = dict([(kuid, specified[kuid])
                         for kuid in available_kuids if kuid in specified])

    return [
        {
            'data': stats_by_kuid,
            'style': chart_styles.get(kuid, default_style),
            'kuid': kuid,
        } for kuid in available_kuids
    ]