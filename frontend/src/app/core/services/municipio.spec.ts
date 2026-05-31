import { TestBed } from '@angular/core/testing';

import { Municipio } from './municipio';

describe('Municipio', () => {
  let service: Municipio;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Municipio);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
