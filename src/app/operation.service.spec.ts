import { TestBed } from '@angular/core/testing';

import { OperationService } from './operation.service';
import {HttpClientModule} from "@angular/common/http";

describe('OperationService', () => {
  let service: OperationService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientModule]
    });
    service = TestBed.inject(OperationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
