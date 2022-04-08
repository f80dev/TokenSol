import { TestBed } from '@angular/core/testing';

import { NftstorageService } from './nftstorage.service';

describe('NftstorageService', () => {
  let service: NftstorageService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(NftstorageService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
