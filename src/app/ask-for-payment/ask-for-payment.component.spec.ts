import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AskForPaymentComponent } from './ask-for-payment.component';

describe('AskForPaymentComponent', () => {
  let component: AskForPaymentComponent;
  let fixture: ComponentFixture<AskForPaymentComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AskForPaymentComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AskForPaymentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
