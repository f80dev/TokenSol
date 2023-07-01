import { TestBed } from '@angular/core/testing';

import { EvmWalletServiceService } from './evm-wallet-service.service';

describe('EvmWalletServiceService', () => {
  let service: EvmWalletServiceService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(EvmWalletServiceService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
