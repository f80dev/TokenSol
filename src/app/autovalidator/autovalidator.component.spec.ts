import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AutovalidatorComponent } from './autovalidator.component';

describe('AutovalidatorComponent', () => {
  let component: AutovalidatorComponent;
  let fixture: ComponentFixture<AutovalidatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AutovalidatorComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AutovalidatorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
