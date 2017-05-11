import React from 'react/addons';
import {KoboMatrix} from './build.kobomatrix';

/*
Initially, this KoboMatrixRow class will be an intermediary between
the react interface and the backbone `model.row` code.
*/
class KoboMatrixRow {
  constructor (model) {
    this._original = model;
    this.label = model.getValue('label');
    this.items = this._original.items.options;
    this.cols = this._original._kobomatrix_columns.models;
  }
}

export function renderKobomatrix (view) {
  let $el = view.$el;
  let model = view.model;
  React.render(<KoboMatrix model={new KoboMatrixRow(model)} />, $el.get(0));
}
