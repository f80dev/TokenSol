import { TestBed } from '@angular/core/testing';

import { MetabossService } from './metaboss.service';

describe('MetabossService', () => {
  let service: MetabossService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MetabossService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
