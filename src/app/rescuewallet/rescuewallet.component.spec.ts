import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RescuewalletComponent } from './rescuewallet.component';

describe('RescuewalletComponent', () => {
  let component: RescuewalletComponent;
  let fixture: ComponentFixture<RescuewalletComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ RescuewalletComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(RescuewalletComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
