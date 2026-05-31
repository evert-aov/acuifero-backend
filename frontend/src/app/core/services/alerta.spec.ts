import { TestBed } from '@angular/core/testing';

import { Alerta } from './alerta';

describe('Alerta', () => {
  let service: Alerta;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Alerta);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
