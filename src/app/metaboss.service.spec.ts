import { TestBed } from '@angular/core/testing';

import { MetabossService } from './metaboss.service';
import {HttpClientModule} from "@angular/common/http";

describe('MetabossService', () => {
  let service: MetabossService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientModule]
    });
    service = TestBed.inject(MetabossService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
